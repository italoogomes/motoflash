"""
Rotas de Clientes

🔒 PROTEÇÃO MULTI-TENANT:
- Todos os clientes são vinculados ao restaurant_id do usuário logado
- Listagem filtra apenas clientes do restaurante do usuário
"""
from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from database import get_session
from models import Customer, CustomerCreate, CustomerUpdate, CustomerResponse, User
from services.auth_service import get_current_user

router = APIRouter(prefix="/customers", tags=["Clientes"])


# ============ CRIAR CLIENTE ============

@router.post("", response_model=CustomerResponse)
def create_customer(
    data: CustomerCreate, 
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Cadastra um novo cliente
    
    🔒 O cliente é vinculado automaticamente ao restaurante do usuário logado
    """
    
    # Verifica se já existe cliente com esse telefone NO MESMO RESTAURANTE
    existing = session.exec(
        select(Customer).where(
            Customer.phone == data.phone,
            Customer.restaurant_id == current_user.restaurant_id  # 🔒
        )
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400, 
            detail="Já existe cliente com este telefone"
        )
    
    # Cria o cliente vinculado ao restaurante
    customer = Customer(
        phone=data.phone,
        name=data.name,
        address=data.address,
        complement=data.complement,
        reference=data.reference,
        lat=None,
        lng=None,
        restaurant_id=current_user.restaurant_id  # 🔒 PROTEÇÃO
    )
    
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


# ============ LISTAR CLIENTES ============

@router.get("", response_model=List[CustomerResponse])
def list_customers(
    search: str = None,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Lista clientes do restaurante do usuário logado
    
    🔒 Filtra automaticamente pelo restaurant_id
    """
    
    # 🔒 Filtra por restaurante
    query = select(Customer).where(
        Customer.restaurant_id == current_user.restaurant_id
    ).order_by(Customer.name)
    
    if search:
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

@router.get("/phone/{phone}", response_model=CustomerResponse)
def get_customer_by_phone(
    phone: str, 
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Busca cliente pelo telefone (apenas do próprio restaurante)
    
    🔒 Filtra pelo restaurant_id
    """
    
    # 🔒 Busca apenas no restaurante do usuário
    customer = session.exec(
        select(Customer).where(
            Customer.phone == phone,
            Customer.restaurant_id == current_user.restaurant_id
        )
    ).first()
    
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

@router.get("/{customer_id}", response_model=CustomerResponse)
def get_customer(
    customer_id: str, 
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Busca cliente pelo ID (apenas do próprio restaurante)"""
    
    customer = session.get(Customer, customer_id)
    
    if not customer:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    
    # 🔒 Verifica se pertence ao restaurante
    if customer.restaurant_id != current_user.restaurant_id:
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

@router.put("/{customer_id}", response_model=CustomerResponse)
def update_customer(
    customer_id: str,
    data: CustomerUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Atualiza dados do cliente (apenas do próprio restaurante)
    
    🔒 Verifica se o cliente pertence ao restaurante
    """
    
    customer = session.get(Customer, customer_id)
    
    if not customer:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    
    # 🔒 Verifica se pertence ao restaurante
    if customer.restaurant_id != current_user.restaurant_id:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    
    # Atualiza só os campos que vieram preenchidos
    if data.phone is not None:
        customer.phone = data.phone
    if data.name is not None:
        customer.name = data.name
    if data.address is not None:
        customer.address = data.address
    if data.complement is not None:
        customer.complement = data.complement
    if data.reference is not None:
        customer.reference = data.reference
    
    customer.updated_at = datetime.now()
    
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

@router.delete("/{customer_id}")
def delete_customer(
    customer_id: str, 
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Remove um cliente (apenas do próprio restaurante)"""
    
    customer = session.get(Customer, customer_id)
    
    if not customer:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    
    # 🔒 Verifica se pertence ao restaurante
    if customer.restaurant_id != current_user.restaurant_id:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    
    session.delete(customer)
    session.commit()
    
    return {"message": "Cliente removido"}
