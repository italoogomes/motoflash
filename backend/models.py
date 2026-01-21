"""
Modelos de dados do sistema de entregas

MULTI-RESTAURANTE (SaaS)
- Cada restaurante tem seus próprios dados isolados
- Sistema de trial de 14 dias + planos pagos
- Autenticação JWT por usuário
"""
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
import uuid


class OrderStatus(str, Enum):
    CREATED = "created"           # Pedido criado
    PREPARING = "preparing"       # Em preparo na cozinha
    READY = "ready"               # Pronto (QR bipado)
    ASSIGNED = "assigned"         # Atribuído a um motoqueiro
    PICKED_UP = "picked_up"       # Coletado pelo motoqueiro
    DELIVERED = "delivered"       # Entregue ao cliente


class PrepType(str, Enum):
    SHORT = "short"   # Preparo rápido (lanches, bebidas)
    LONG = "long"     # Preparo demorado (pizzas, pratos)


class CourierStatus(str, Enum):
    AVAILABLE = "available"   # Disponível para entregas
    BUSY = "busy"             # Em entrega
    OFFLINE = "offline"       # Fora de serviço


class BatchStatus(str, Enum):
    ASSIGNED = "assigned"       # Lote criado e atribuído
    IN_PROGRESS = "in_progress" # Motoqueiro em rota
    DONE = "done"               # Todas entregas feitas


# ============ NOVOS ENUMS (MULTI-RESTAURANTE) ============

class PlanType(str, Enum):
    """Planos disponíveis"""
    TRIAL = "trial"       # Teste grátis (14 dias)
    BASIC = "basic"       # Plano básico (R$ 79/mês)
    PRO = "pro"           # Plano profissional (R$ 149/mês)


class UserRole(str, Enum):
    """Papéis de usuário"""
    OWNER = "owner"       # Dono do restaurante (acesso total)
    MANAGER = "manager"   # Gerente (acesso limitado)


# ============ TABELAS MULTI-RESTAURANTE ============

class Restaurant(SQLModel, table=True):
    """
    Restaurante/Estabelecimento
    
    Cada restaurante é um "inquilino" do sistema (multi-tenant).
    Todos os dados (pedidos, motoboys, clientes) são vinculados aqui.
    """
    __tablename__ = "restaurants"
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    
    # Identificador único na URL (ex: pizzaria-do-ze)
    slug: str = Field(index=True, unique=True)
    
    # Dados básicos
    name: str                                    # Nome do restaurante
    email: str = Field(index=True, unique=True)  # Email principal
    phone: Optional[str] = None
    cnpj: Optional[str] = None
    logo_url: Optional[str] = None
    
    # Endereço (com geocoding automático no cadastro)
    address: str = ""
    lat: Optional[float] = None
    lng: Optional[float] = None
    
    # Plano e trial
    plan: PlanType = Field(default=PlanType.TRIAL)
    trial_ends_at: datetime = Field(
        default_factory=lambda: datetime.now() + timedelta(days=14)
    )
    blocked: bool = Field(default=False)  # True quando trial vence sem pagar
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    def is_trial_expired(self) -> bool:
        """Verifica se o trial expirou"""
        return self.plan == PlanType.TRIAL and datetime.now() > self.trial_ends_at
    
    def days_remaining(self) -> int:
        """Dias restantes do trial"""
        if self.plan != PlanType.TRIAL:
            return -1  # Plano pago, não tem limite
        delta = self.trial_ends_at - datetime.now()
        return max(0, delta.days)


class User(SQLModel, table=True):
    """
    Usuário do sistema (dono ou funcionário)
    
    Cada usuário pertence a UM restaurante.
    Autenticação via email + senha (hash).
    """
    __tablename__ = "users"
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    
    # Dados do usuário
    name: str
    email: str = Field(index=True, unique=True)
    password_hash: str  # Senha criptografada (bcrypt)
    
    # Vínculo com restaurante
    restaurant_id: str = Field(foreign_key="restaurants.id")
    role: UserRole = Field(default=UserRole.OWNER)
    
    # Status
    active: bool = Field(default=True)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    last_login: Optional[datetime] = None


# ============ TABELAS EXISTENTES (com restaurant_id) ============

class Customer(SQLModel, table=True):
    """
    Cliente do restaurante
    
    Pensa assim: essa classe é como um FORMULÁRIO em branco.
    Cada linha abaixo é um CAMPO desse formulário.
    """
    __tablename__ = "customers"  # Nome da "gaveta" no banco de dados
    
    # ID único - como o CPF, cada cliente tem um número só dele
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    
    # NOVO: Vínculo com restaurante (isolamento de dados)
    restaurant_id: Optional[str] = Field(default=None, foreign_key="restaurants.id", index=True)
    
    # Telefone - é a "chave" pra buscar o cliente (tipo RG)
    phone: str = Field(index=True)  # index=True = busca mais rápida
    
    # Nome do cliente
    name: str
    
    # Endereço completo (rua, número, bairro)
    address: str
    
    # Complemento - opcional (pode ser vazio)
    complement: Optional[str] = None  # Optional = não é obrigatório
    
    # Ponto de referência - opcional
    reference: Optional[str] = None
    
    # Coordenadas - pra não precisar buscar no Google toda vez
    lat: Optional[float] = None
    lng: Optional[float] = None
    
    # Quando foi criado e atualizado
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class Category(SQLModel, table=True):
    """Categoria do cardápio (ex: Hambúrgueres, Bebidas, Sobremesas)"""
    __tablename__ = "categories"
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    
    # NOVO: Vínculo com restaurante
    restaurant_id: Optional[str] = Field(default=None, foreign_key="restaurants.id", index=True)
    
    name: str
    order: int = Field(default=0)  # Ordem de exibição
    active: bool = Field(default=True)
    
    created_at: datetime = Field(default_factory=datetime.now)


class MenuItem(SQLModel, table=True):
    """Item do cardápio"""
    __tablename__ = "menu_items"
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    
    # NOVO: Vínculo com restaurante
    restaurant_id: Optional[str] = Field(default=None, foreign_key="restaurants.id", index=True)
    
    name: str
    description: Optional[str] = None
    price: float
    image_url: Optional[str] = None
    
    category_id: str = Field(foreign_key="categories.id")
    
    active: bool = Field(default=True)  # Se está disponível
    out_of_stock: bool = Field(default=False)  # Esgotado temporariamente
    
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class Order(SQLModel, table=True):
    """Pedido do restaurante"""
    __tablename__ = "orders"
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    
    # NOVO: Vínculo com restaurante
    restaurant_id: Optional[str] = Field(default=None, foreign_key="restaurants.id", index=True)
    
    # Informações do pedido
    customer_name: str = Field(default="Cliente")
    address_text: str
    lat: float
    lng: float
    
    # Tipo de preparo e status
    prep_type: PrepType = Field(default=PrepType.SHORT)
    status: OrderStatus = Field(default=OrderStatus.CREATED)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    ready_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    
    # Relacionamentos
    batch_id: Optional[str] = Field(default=None, foreign_key="batches.id")
    stop_order: Optional[int] = None  # Ordem de parada no lote (1, 2, 3...)


class Courier(SQLModel, table=True):
    """Motoqueiro"""
    __tablename__ = "couriers"
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    
    # NOVO: Vínculo com restaurante
    restaurant_id: Optional[str] = Field(default=None, foreign_key="restaurants.id", index=True)
    
    name: str
    phone: Optional[str] = None
    
    status: CourierStatus = Field(default=CourierStatus.AVAILABLE)
    
    # Última posição conhecida (para cálculo de proximidade)
    last_lat: Optional[float] = None
    last_lng: Optional[float] = None
    
    # Token para Push Notifications (Firebase Cloud Messaging)
    push_token: Optional[str] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    available_since: Optional[datetime] = None  # Quando ficou disponível


class Batch(SQLModel, table=True):
    """Lote de entregas (conjunto de pedidos para um motoqueiro)"""
    __tablename__ = "batches"
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    
    # NOVO: Vínculo com restaurante
    restaurant_id: Optional[str] = Field(default=None, foreign_key="restaurants.id", index=True)
    
    courier_id: str = Field(foreign_key="couriers.id")
    status: BatchStatus = Field(default=BatchStatus.ASSIGNED)
    
    created_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None


# ============ SCHEMAS (para API) ============

class OrderCreate(SQLModel):
    """Schema para criar pedido"""
    customer_name: str = "Cliente"
    address_text: str
    lat: Optional[float] = None  # Se não informado, usa geocoding
    lng: Optional[float] = None  # Se não informado, usa geocoding
    prep_type: PrepType = PrepType.SHORT
    simulated_date: Optional[str] = None  # Para simulação: "2025-01-14"


class OrderResponse(SQLModel):
    """Schema de resposta do pedido"""
    id: str
    customer_name: str
    address_text: str
    lat: float
    lng: float
    prep_type: PrepType
    status: OrderStatus
    created_at: datetime
    ready_at: Optional[datetime]
    batch_id: Optional[str]
    stop_order: Optional[int]


class CourierCreate(SQLModel):
    """Schema para criar motoqueiro"""
    name: str
    phone: Optional[str] = None


class CourierResponse(SQLModel):
    """Schema de resposta do motoqueiro"""
    id: str
    name: str
    phone: Optional[str]
    status: CourierStatus
    available_since: Optional[datetime]


class BatchResponse(SQLModel):
    """Schema de resposta do lote"""
    id: str
    courier_id: str
    courier_name: Optional[str] = None
    status: BatchStatus
    created_at: datetime
    orders: List[OrderResponse] = []


class DispatchResult(SQLModel):
    """Resultado do algoritmo de dispatch"""
    batches_created: int
    orders_assigned: int
    message: str


# ============ SCHEMAS DO CARDÁPIO ============

class CategoryCreate(SQLModel):
    """Schema para criar categoria"""
    name: str
    order: int = 0


class CategoryUpdate(SQLModel):
    """Schema para atualizar categoria"""
    name: Optional[str] = None
    order: Optional[int] = None
    active: Optional[bool] = None


class CategoryResponse(SQLModel):
    """Schema de resposta da categoria"""
    id: str
    name: str
    order: int
    active: bool
    items_count: Optional[int] = 0


class MenuItemCreate(SQLModel):
    """Schema para criar item do cardápio"""
    name: str
    description: Optional[str] = None
    price: float
    image_url: Optional[str] = None
    category_id: str


class MenuItemUpdate(SQLModel):
    """Schema para atualizar item"""
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    image_url: Optional[str] = None
    category_id: Optional[str] = None
    active: Optional[bool] = None
    out_of_stock: Optional[bool] = None


class MenuItemResponse(SQLModel):
    """Schema de resposta do item"""
    id: str
    name: str
    description: Optional[str]
    price: float
    image_url: Optional[str]
    category_id: str
    category_name: Optional[str] = None
    active: bool
    out_of_stock: bool


# ============ SCHEMAS DO CLIENTE ============

class CustomerCreate(SQLModel):
    """
    Schema para CRIAR cliente
    
    Pensa assim: é o FORMULÁRIO que o atendente preenche
    pra cadastrar um cliente novo.
    
    Campos obrigatórios: phone, name, address
    Campos opcionais: complement, reference
    """
    phone: str           # Obrigatório
    name: str            # Obrigatório
    address: str         # Obrigatório
    complement: Optional[str] = None   # Opcional
    reference: Optional[str] = None    # Opcional


class CustomerUpdate(SQLModel):
    """
    Schema para ATUALIZAR cliente
    
    Aqui TUDO é opcional (Optional) porque você pode
    querer mudar só o endereço, ou só o nome, etc.
    """
    phone: Optional[str] = None
    name: Optional[str] = None
    address: Optional[str] = None
    complement: Optional[str] = None
    reference: Optional[str] = None


class CustomerResponse(SQLModel):
    """
    Schema de RESPOSTA do cliente
    
    É o que a API DEVOLVE quando você busca um cliente.
    Tem todos os campos, incluindo id, lat, lng, etc.
    """
    id: str
    phone: str
    name: str
    address: str
    complement: Optional[str]
    reference: Optional[str]
    lat: Optional[float]
    lng: Optional[float]
    created_at: datetime


# ============ CONFIGURAÇÕES DO RESTAURANTE ============

class Settings(SQLModel, table=True):
    """
    Configurações do restaurante
    
    Essa tabela tem só UMA linha - os dados do restaurante.
    O endereço e coordenadas ficam salvos aqui, assim não
    precisa chamar Geocoding toda vez que abrir o app!
    """
    __tablename__ = "settings"
    
    id: str = Field(default="default", primary_key=True)  # Sempre "default"
    
    # Dados do restaurante
    restaurant_name: str = Field(default="Meu Restaurante")
    phone: Optional[str] = None
    
    # Endereço (texto)
    address: str = Field(default="")
    
    # Coordenadas (já geocodificadas - NÃO chama API toda vez!)
    lat: Optional[float] = None
    lng: Optional[float] = None
    
    # Quando foi atualizado
    updated_at: datetime = Field(default_factory=datetime.now)


class SettingsUpdate(SQLModel):
    """Schema para atualizar configurações"""
    restaurant_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None  # Se mudar, recalcula lat/lng


class SettingsResponse(SQLModel):
    """Schema de resposta das configurações"""
    id: str
    restaurant_name: str
    phone: Optional[str]
    address: str
    lat: Optional[float]
    lng: Optional[float]
    updated_at: datetime


# ============ SCHEMAS MULTI-RESTAURANTE ============

class RestaurantCreate(SQLModel):
    """Schema para cadastrar restaurante"""
    name: str                           # Nome do restaurante
    email: str                          # Email principal (será o login)
    password: str                       # Senha (será hasheada)
    phone: Optional[str] = None
    address: str                        # Endereço (geocoding automático)
    cnpj: Optional[str] = None


class RestaurantUpdate(SQLModel):
    """Schema para atualizar restaurante"""
    name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None       # Se mudar, recalcula lat/lng
    cnpj: Optional[str] = None
    logo_url: Optional[str] = None


class RestaurantResponse(SQLModel):
    """Schema de resposta do restaurante"""
    id: str
    slug: str
    name: str
    email: str
    phone: Optional[str]
    cnpj: Optional[str]
    logo_url: Optional[str]
    address: str
    lat: Optional[float]
    lng: Optional[float]
    plan: PlanType
    trial_ends_at: datetime
    blocked: bool
    days_remaining: int                 # Calculado dinamicamente
    created_at: datetime


class UserCreate(SQLModel):
    """Schema para criar usuário (funcionário)"""
    name: str
    email: str
    password: str
    role: UserRole = UserRole.MANAGER


class UserUpdate(SQLModel):
    """Schema para atualizar usuário"""
    name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None      # Nova senha (será hasheada)
    role: Optional[UserRole] = None
    active: Optional[bool] = None


class UserResponse(SQLModel):
    """Schema de resposta do usuário"""
    id: str
    name: str
    email: str
    restaurant_id: str
    role: UserRole
    active: bool
    created_at: datetime
    last_login: Optional[datetime]


class LoginRequest(SQLModel):
    """Schema para login"""
    email: str
    password: str


class LoginResponse(SQLModel):
    """Schema de resposta do login"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
    restaurant: RestaurantResponse