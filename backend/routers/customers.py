"""
Rotas de Clientes

EXPLICAÇÃO SIMPLES:
Este arquivo é como um "balcão de atendimento".
Cada função é uma AÇÃO que alguém pode pedir:
- "Quero cadastrar um cliente" → create_customer
- "Quero ver todos os clientes" → list_customers
- "Quero buscar pelo telefone" → get_customer_by_phone
"""
from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from database import get_session
from models import Customer, CustomerCreate, CustomerUpdate, CustomerResponse

# Cria o "balcão" de clientes
# prefix="/customers" = todas as rotas começam com /customers
# tags=["Clientes"] = organiza na documentação
router = APIRouter(prefix="/customers", tags=["Clientes"])


# ============ CRIAR CLIENTE ============
# POST /customers
# 
# POST = "Quero CRIAR algo novo"
# É como preencher uma ficha e entregar pro atendente

@router.post("", response_model=CustomerResponse)
def create_customer(data: CustomerCreate, session: Session = Depends(get_session)):
    """
    Cadastra um novo cliente
    
    O que acontece aqui:
    1. Recebe os dados (telefone, nome, endereço)
    2. Verifica se já existe cliente com esse telefone
    3. Salva no banco de dados (sem coordenadas - economiza Geocoding!)
    4. Coordenadas são buscadas apenas ao criar pedido
    """
    
    # 1. Verifica se já existe cliente com esse telefone
    existing = session.exec(
        select(Customer).where(Customer.phone == data.phone)
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400, 
            detail="Já existe cliente com este telefone"
        )
    
    # 2. Cria o cliente (sem coordenadas - serão buscadas apenas ao criar pedido)
    customer = Customer(
        phone=data.phone,
        name=data.name,
        address=data.address,
        complement=data.complement,
        reference=data.reference,
        lat=None,
        lng=None
    )
    
    # 3. Salva no banco
    # session.add() = "Coloca na gaveta"
    # session.commit() = "Confirma que salvou"
    # session.refresh() = "Atualiza com os dados do banco (pega o id gerado)"
    session.add(customer)
    session.commit()
    session.refresh(customer)
    
    # 4. Devolve o cliente criado
    return CustomerResponse(
        id=customer.id,
        phone=customer.phone,
        name=customer.name,
        address=customer.address,
        complement=customer.complement,
        reference=customer.reference,
        lat=customer.lat,
        lng=customer.lng,
        created_at=customer.created_at
    )


# ============ LISTAR CLIENTES ============
# GET /customers
#
# GET = "Quero VER/BUSCAR algo"
# É como pedir pra ver todas as fichas da gaveta

@router.get("", response_model=List[CustomerResponse])
def list_customers(
    search: str = None,  # Parâmetro opcional pra filtrar
    session: Session = Depends(get_session)
):
    """
    Lista todos os clientes
    
    Pode filtrar por nome ou telefone usando ?search=texto
    Exemplo: /customers?search=joao
    """
    
    # Começa a busca
    query = select(Customer).order_by(Customer.name)
    
    # Se passou um filtro, aplica
    if search:
        # ilike = busca ignorando maiúsculas/minúsculas
        # % = qualquer coisa antes ou depois
        search_term = f"%{search}%"
        query = query.where(
            (Customer.name.ilike(search_term)) | 
            (Customer.phone.ilike(search_term))
        )
    
    customers = session.exec(query).all()
    
    return [
        CustomerResponse(
            id=c.id,
            phone=c.phone,
            name=c.name,
            address=c.address,
            complement=c.complement,
            reference=c.reference,
            lat=c.lat,
            lng=c.lng,
            created_at=c.created_at
        )
        for c in customers
    ]


# ============ BUSCAR POR TELEFONE ============
# GET /customers/phone/{phone}
#
# Essa é a MÁGICA pro formulário de pedido!
# Digita o telefone → aparece os dados do cliente

@router.get("/phone/{phone}", response_model=CustomerResponse)
def get_customer_by_phone(phone: str, session: Session = Depends(get_session)):
    """
    Busca cliente pelo telefone
    
    Essa rota é usada no formulário de novo pedido:
    - Atendente digita telefone
    - Sistema busca se já existe
    - Se existe, preenche nome e endereço automaticamente!
    """
    
    # Busca no banco
    customer = session.exec(
        select(Customer).where(Customer.phone == phone)
    ).first()
    
    # Se não encontrou, retorna erro 404 (Não encontrado)
    if not customer:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    
    return CustomerResponse(
        id=customer.id,
        phone=customer.phone,
        name=customer.name,
        address=customer.address,
        complement=customer.complement,
        reference=customer.reference,
        lat=customer.lat,
        lng=customer.lng,
        created_at=customer.created_at
    )


# ============ BUSCAR POR ID ============
# GET /customers/{customer_id}

@router.get("/{customer_id}", response_model=CustomerResponse)
def get_customer(customer_id: str, session: Session = Depends(get_session)):
    """Busca cliente pelo ID"""
    
    customer = session.get(Customer, customer_id)
    
    if not customer:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    
    return CustomerResponse(
        id=customer.id,
        phone=customer.phone,
        name=customer.name,
        address=customer.address,
        complement=customer.complement,
        reference=customer.reference,
        lat=customer.lat,
        lng=customer.lng,
        created_at=customer.created_at
    )


# ============ ATUALIZAR CLIENTE ============
# PUT /customers/{customer_id}
#
# PUT = "Quero ATUALIZAR algo que já existe"
# É como pegar uma ficha e corrigir alguns campos

@router.put("/{customer_id}", response_model=CustomerResponse)
def update_customer(
    customer_id: str,
    data: CustomerUpdate,
    session: Session = Depends(get_session)
):
    """
    Atualiza dados do cliente
    
    Só atualiza os campos que foram enviados.
    Se mandar só o nome, só o nome muda.
    """
    
    # Busca o cliente
    customer = session.get(Customer, customer_id)
    
    if not customer:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    
    # Atualiza só os campos que vieram preenchidos
    # "if data.X is not None" = "se mandou esse campo"
    if data.phone is not None:
        customer.phone = data.phone
    if data.name is not None:
        customer.name = data.name
    if data.address is not None:
        customer.address = data.address
        # Coordenadas serão atualizadas apenas ao criar novo pedido
    if data.complement is not None:
        customer.complement = data.complement
    if data.reference is not None:
        customer.reference = data.reference
    
    # Atualiza a data de modificação
    customer.updated_at = datetime.now()
    
    # Salva
    session.add(customer)
    session.commit()
    session.refresh(customer)
    
    return CustomerResponse(
        id=customer.id,
        phone=customer.phone,
        name=customer.name,
        address=customer.address,
        complement=customer.complement,
        reference=customer.reference,
        lat=customer.lat,
        lng=customer.lng,
        created_at=customer.created_at
    )


# ============ DELETAR CLIENTE ============
# DELETE /customers/{customer_id}
#
# DELETE = "Quero REMOVER algo"
# É como jogar a ficha fora

@router.delete("/{customer_id}")
def delete_customer(customer_id: str, session: Session = Depends(get_session)):
    """Remove um cliente"""
    
    customer = session.get(Customer, customer_id)
    
    if not customer:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    
    session.delete(customer)
    session.commit()
    
    return {"message": "Cliente removido"}