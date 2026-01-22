"""
Rotas do Cardápio (Categorias e Itens)

🔒 PROTEÇÃO MULTI-TENANT:
- Todas as categorias e itens são vinculados ao restaurant_id do usuário logado
- Listagem filtra apenas dados do restaurante do usuário
"""
from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, func

from database import get_session
from models import (
    Category, CategoryCreate, CategoryUpdate, CategoryResponse,
    MenuItem, MenuItemCreate, MenuItemUpdate, MenuItemResponse,
    User
)
from services.auth_service import get_current_user

router = APIRouter(prefix="/menu", tags=["Cardápio"])


# ============ CATEGORIAS ============

@router.post("/categories", response_model=CategoryResponse)
def create_category(
    data: CategoryCreate, 
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Cria uma nova categoria
    
    🔒 Vincula ao restaurante do usuário logado
    """
    category = Category(
        name=data.name,
        order=data.order,
        restaurant_id=current_user.restaurant_id  # 🔒 PROTEÇÃO
    )
    
    session.add(category)
    session.commit()
    session.refresh(category)
    
    return CategoryResponse(
        id=category.id,
        name=category.name,
        order=category.order,
        active=category.active,
        items_count=0
    )


@router.get("/categories", response_model=List[CategoryResponse])
def list_categories(
    include_inactive: bool = False,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Lista todas as categorias com contagem de itens
    
    🔒 Filtra por restaurant_id
    """
    # 🔒 Filtra por restaurante
    query = select(Category).where(
        Category.restaurant_id == current_user.restaurant_id
    ).order_by(Category.order, Category.name)
    
    if not include_inactive:
        query = query.where(Category.active == True)
    
    categories = session.exec(query).all()
    
    result = []
    for cat in categories:
        # Conta itens da categoria (do mesmo restaurante)
        items_query = select(func.count(MenuItem.id)).where(
            MenuItem.category_id == cat.id,
            MenuItem.restaurant_id == current_user.restaurant_id  # 🔒
        )
        if not include_inactive:
            items_query = items_query.where(MenuItem.active == True)
        items_count = session.exec(items_query).one()
        
        result.append(CategoryResponse(
            id=cat.id,
            name=cat.name,
            order=cat.order,
            active=cat.active,
            items_count=items_count
        ))
    
    return result


@router.get("/categories/{category_id}", response_model=CategoryResponse)
def get_category(
    category_id: str, 
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Busca uma categoria pelo ID (apenas do próprio restaurante)"""
    category = session.get(Category, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")
    
    # 🔒 Verifica se pertence ao restaurante
    if category.restaurant_id != current_user.restaurant_id:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")
    
    items_query = select(func.count(MenuItem.id)).where(MenuItem.category_id == category.id)
    items_count = session.exec(items_query).one()
    
    return CategoryResponse(
        id=category.id,
        name=category.name,
        order=category.order,
        active=category.active,
        items_count=items_count
    )


@router.put("/categories/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: str,
    data: CategoryUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Atualiza uma categoria (apenas do próprio restaurante)"""
    category = session.get(Category, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")
    
    # 🔒 Verifica se pertence ao restaurante
    if category.restaurant_id != current_user.restaurant_id:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")
    
    if data.name is not None:
        category.name = data.name
    if data.order is not None:
        category.order = data.order
    if data.active is not None:
        category.active = data.active
    
    session.add(category)
    session.commit()
    session.refresh(category)
    
    items_query = select(func.count(MenuItem.id)).where(MenuItem.category_id == category.id)
    items_count = session.exec(items_query).one()
    
    return CategoryResponse(
        id=category.id,
        name=category.name,
        order=category.order,
        active=category.active,
        items_count=items_count
    )


@router.delete("/categories/{category_id}")
def delete_category(
    category_id: str, 
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Remove uma categoria (se não tiver itens) - apenas do próprio restaurante"""
    category = session.get(Category, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")
    
    # 🔒 Verifica se pertence ao restaurante
    if category.restaurant_id != current_user.restaurant_id:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")
    
    # Verifica se tem itens
    items_query = select(func.count(MenuItem.id)).where(MenuItem.category_id == category_id)
    items_count = session.exec(items_query).one()
    
    if items_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Categoria tem {items_count} item(ns). Remova os itens primeiro."
        )
    
    session.delete(category)
    session.commit()
    
    return {"message": "Categoria removida"}


# ============ ITENS ============

@router.post("/items", response_model=MenuItemResponse)
def create_item(
    data: MenuItemCreate, 
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Cria um novo item no cardápio
    
    🔒 Vincula ao restaurante do usuário logado
    """
    # Verifica se categoria existe E pertence ao restaurante
    category = session.get(Category, data.category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")
    
    # 🔒 Verifica se categoria pertence ao restaurante
    if category.restaurant_id != current_user.restaurant_id:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")
    
    item = MenuItem(
        name=data.name,
        description=data.description,
        price=data.price,
        image_url=data.image_url,
        category_id=data.category_id,
        restaurant_id=current_user.restaurant_id  # 🔒 PROTEÇÃO
    )
    
    session.add(item)
    session.commit()
    session.refresh(item)
    
    return MenuItemResponse(
        id=item.id,
        name=item.name,
        description=item.description,
        price=item.price,
        image_url=item.image_url,
        category_id=item.category_id,
        category_name=category.name,
        active=item.active,
        out_of_stock=item.out_of_stock
    )


@router.get("/items", response_model=List[MenuItemResponse])
def list_items(
    category_id: str = None,
    include_inactive: bool = False,
    include_out_of_stock: bool = True,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Lista itens do cardápio, opcionalmente filtrados por categoria
    
    🔒 Filtra por restaurant_id
    """
    # 🔒 Filtra por restaurante
    query = select(MenuItem).where(
        MenuItem.restaurant_id == current_user.restaurant_id
    ).order_by(MenuItem.name)
    
    if category_id:
        query = query.where(MenuItem.category_id == category_id)
    
    if not include_inactive:
        query = query.where(MenuItem.active == True)
    
    if not include_out_of_stock:
        query = query.where(MenuItem.out_of_stock == False)
    
    items = session.exec(query).all()
    
    result = []
    for item in items:
        category = session.get(Category, item.category_id)
        result.append(MenuItemResponse(
            id=item.id,
            name=item.name,
            description=item.description,
            price=item.price,
            image_url=item.image_url,
            category_id=item.category_id,
            category_name=category.name if category else None,
            active=item.active,
            out_of_stock=item.out_of_stock
        ))
    
    return result


@router.get("/items/{item_id}", response_model=MenuItemResponse)
def get_item(
    item_id: str, 
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Busca um item pelo ID (apenas do próprio restaurante)"""
    item = session.get(MenuItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    
    # 🔒 Verifica se pertence ao restaurante
    if item.restaurant_id != current_user.restaurant_id:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    
    category = session.get(Category, item.category_id)
    
    return MenuItemResponse(
        id=item.id,
        name=item.name,
        description=item.description,
        price=item.price,
        image_url=item.image_url,
        category_id=item.category_id,
        category_name=category.name if category else None,
        active=item.active,
        out_of_stock=item.out_of_stock
    )


@router.put("/items/{item_id}", response_model=MenuItemResponse)
def update_item(
    item_id: str,
    data: MenuItemUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Atualiza um item (apenas do próprio restaurante)"""
    item = session.get(MenuItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    
    # 🔒 Verifica se pertence ao restaurante
    if item.restaurant_id != current_user.restaurant_id:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    
    if data.name is not None:
        item.name = data.name
    if data.description is not None:
        item.description = data.description
    if data.price is not None:
        item.price = data.price
    if data.image_url is not None:
        item.image_url = data.image_url
    if data.category_id is not None:
        # Verifica se nova categoria existe E pertence ao restaurante
        category = session.get(Category, data.category_id)
        if not category or category.restaurant_id != current_user.restaurant_id:
            raise HTTPException(status_code=404, detail="Categoria não encontrada")
        item.category_id = data.category_id
    if data.active is not None:
        item.active = data.active
    if data.out_of_stock is not None:
        item.out_of_stock = data.out_of_stock
    
    item.updated_at = datetime.now()
    
    session.add(item)
    session.commit()
    session.refresh(item)
    
    category = session.get(Category, item.category_id)
    
    return MenuItemResponse(
        id=item.id,
        name=item.name,
        description=item.description,
        price=item.price,
        image_url=item.image_url,
        category_id=item.category_id,
        category_name=category.name if category else None,
        active=item.active,
        out_of_stock=item.out_of_stock
    )


@router.delete("/items/{item_id}")
def delete_item(
    item_id: str, 
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Remove um item do cardápio (apenas do próprio restaurante)"""
    item = session.get(MenuItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    
    # 🔒 Verifica se pertence ao restaurante
    if item.restaurant_id != current_user.restaurant_id:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    
    session.delete(item)
    session.commit()
    
    return {"message": "Item removido"}


@router.post("/items/{item_id}/toggle-stock", response_model=MenuItemResponse)
def toggle_stock(
    item_id: str, 
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Alterna status de estoque (disponível/esgotado) - apenas do próprio restaurante"""
    item = session.get(MenuItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    
    # 🔒 Verifica se pertence ao restaurante
    if item.restaurant_id != current_user.restaurant_id:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    
    item.out_of_stock = not item.out_of_stock
    item.updated_at = datetime.now()
    
    session.add(item)
    session.commit()
    session.refresh(item)
    
    category = session.get(Category, item.category_id)
    
    return MenuItemResponse(
        id=item.id,
        name=item.name,
        description=item.description,
        price=item.price,
        image_url=item.image_url,
        category_id=item.category_id,
        category_name=category.name if category else None,
        active=item.active,
        out_of_stock=item.out_of_stock
    )


# ============ CARDÁPIO COMPLETO ============

@router.get("/full")
def get_full_menu(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Retorna cardápio completo organizado por categoria
    
    🔒 Filtra por restaurant_id
    """
    # 🔒 Filtra por restaurante
    categories = session.exec(
        select(Category)
        .where(Category.active == True)
        .where(Category.restaurant_id == current_user.restaurant_id)
        .order_by(Category.order, Category.name)
    ).all()
    
    result = []
    for cat in categories:
        # 🔒 Filtra itens por restaurante também
        items = session.exec(
            select(MenuItem)
            .where(MenuItem.category_id == cat.id)
            .where(MenuItem.active == True)
            .where(MenuItem.restaurant_id == current_user.restaurant_id)
            .order_by(MenuItem.name)
        ).all()
        
        result.append({
            "id": cat.id,
            "name": cat.name,
            "items": [
                {
                    "id": item.id,
                    "name": item.name,
                    "description": item.description,
                    "price": item.price,
                    "image_url": item.image_url,
                    "out_of_stock": item.out_of_stock
                }
                for item in items
            ]
        })
    
    return result
