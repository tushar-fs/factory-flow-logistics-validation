"""
FactoryFlow - Inventory Management API
Simple FastAPI app for tracking factory inventory.
"""

from typing import List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from .database import get_db, init_db
from .models import Item


# --- Pydantic Schemas ---

class ItemCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    quantity: int = Field(..., ge=0)
    location: str = Field(..., min_length=1, max_length=100)


class ItemResponse(BaseModel):
    id: int
    name: str
    quantity: int
    location: str
    
    class Config:
        from_attributes = True


class MoveRequest(BaseModel):
    item_name: str
    quantity: int = Field(..., gt=0)
    from_location: str
    to_location: str


class MoveResponse(BaseModel):
    message: str
    from_item: ItemResponse
    to_item: ItemResponse


# --- App Setup ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up...")
    init_db()
    yield
    print("Shutting down...")


app = FastAPI(
    title="FactoryFlow",
    description="Inventory Management System",
    version="1.0.0",
    lifespan=lifespan
)

templates = Jinja2Templates(directory="app/templates")


# --- Health Check ---

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    try:
        db.execute("SELECT 1")
        return {"status": "healthy", "database": "connected", "version": "1.0.0"}
    except Exception as e:
        return {"status": "unhealthy", "database": str(e), "version": "1.0.0"}


# --- API Endpoints ---

@app.get("/inventory", response_model=List[ItemResponse])
def get_inventory(location: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Item)
    if location:
        query = query.filter(Item.location == location)
    return query.all()


@app.post("/inventory", response_model=ItemResponse, status_code=201)
def create_item(item: ItemCreate, db: Session = Depends(get_db)):
    # Check if item exists at this location - update qty instead of duplicating
    existing = db.query(Item).filter(
        Item.name == item.name,
        Item.location == item.location
    ).first()
    
    if existing:
        existing.quantity += item.quantity
        db.commit()
        db.refresh(existing)
        return existing
    
    db_item = Item(name=item.name, quantity=item.quantity, location=item.location)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


@app.post("/move", response_model=MoveResponse)
def move_inventory(move: MoveRequest, db: Session = Depends(get_db)):
    # Find source
    from_item = db.query(Item).filter(
        Item.name == move.item_name,
        Item.location == move.from_location
    ).first()
    
    if not from_item:
        raise HTTPException(404, f"Item '{move.item_name}' not found in '{move.from_location}'")
    
    if from_item.quantity < move.quantity:
        raise HTTPException(400, f"Insufficient quantity. Have: {from_item.quantity}, Need: {move.quantity}")
    
    # Decrease source
    from_item.quantity -= move.quantity
    
    # Find or create destination
    to_item = db.query(Item).filter(
        Item.name == move.item_name,
        Item.location == move.to_location
    ).first()
    
    if to_item:
        to_item.quantity += move.quantity
    else:
        to_item = Item(name=move.item_name, quantity=move.quantity, location=move.to_location)
        db.add(to_item)
    
    db.commit()
    db.refresh(from_item)
    db.refresh(to_item)
    
    return {
        "message": f"Moved {move.quantity} '{move.item_name}' from '{move.from_location}' to '{move.to_location}'",
        "from_item": from_item,
        "to_item": to_item
    }


@app.delete("/inventory/{item_id}")
def delete_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(404, f"Item {item_id} not found")
    
    db.delete(item)
    db.commit()
    return {"message": f"Item {item_id} deleted"}


# --- HTML Frontend ---

@app.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    items = db.query(Item).all()
    locations = db.query(Item.location).distinct().all()
    location_list = [loc[0] for loc in locations] or ["Warehouse A", "Warehouse B", "Warehouse C"]
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "items": items,
        "locations": location_list
    })


@app.post("/add-item-form", response_class=HTMLResponse)
def add_item_form(
    request: Request,
    name: str = Form(...),
    quantity: int = Form(...),
    location: str = Form(...),
    db: Session = Depends(get_db)
):
    existing = db.query(Item).filter(Item.name == name, Item.location == location).first()
    
    if existing:
        existing.quantity += quantity
    else:
        db.add(Item(name=name, quantity=quantity, location=location))
    
    db.commit()
    return RedirectResponse(url="/", status_code=303)


@app.post("/move-item-form", response_class=HTMLResponse)
def move_item_form(
    request: Request,
    item_name: str = Form(...),
    quantity: int = Form(...),
    from_location: str = Form(...),
    to_location: str = Form(...),
    db: Session = Depends(get_db)
):
    from_item = db.query(Item).filter(
        Item.name == item_name,
        Item.location == from_location
    ).first()
    
    if not from_item or from_item.quantity < quantity:
        return RedirectResponse(url="/", status_code=303)
    
    from_item.quantity -= quantity
    
    to_item = db.query(Item).filter(
        Item.name == item_name,
        Item.location == to_location
    ).first()
    
    if to_item:
        to_item.quantity += quantity
    else:
        db.add(Item(name=item_name, quantity=quantity, location=to_location))
    
    db.commit()
    return RedirectResponse(url="/", status_code=303)
