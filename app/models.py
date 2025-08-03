from sqlmodel import SQLModel, Field, Relationship, JSON, Column
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from enum import Enum


class UserRole(str, Enum):
    BUYER = "buyer"
    SELLER = "seller"
    ADMIN = "admin"


class OrderStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    RETURNED = "returned"


class DeliveryStatus(str, Enum):
    PENDING = "pending"
    PICKED_UP = "picked_up"
    IN_TRANSIT = "in_transit"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETURNED = "returned"


# Persistent models (stored in database)
class User(SQLModel, table=True):
    __tablename__ = "users"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, max_length=255, regex=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
    password_hash: str = Field(max_length=255)
    full_name: str = Field(max_length=100)
    phone: Optional[str] = Field(default=None, max_length=20)
    role: UserRole = Field(default=UserRole.BUYER)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    addresses: List["Address"] = Relationship(back_populates="user")
    cart_items: List["CartItem"] = Relationship(back_populates="user")
    orders: List["Order"] = Relationship(back_populates="user")
    products: List["Product"] = Relationship(back_populates="seller")
    seller_profile: Optional["SellerProfile"] = Relationship(back_populates="user")


class Address(SQLModel, table=True):
    __tablename__ = "addresses"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    label: str = Field(max_length=50)  # e.g., "Home", "Office"
    full_address: str = Field(max_length=500)
    city: str = Field(max_length=100)
    state: str = Field(max_length=100)
    postal_code: str = Field(max_length=20)
    country: str = Field(max_length=100, default="Indonesia")
    is_default: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    user: User = Relationship(back_populates="addresses")
    orders: List["Order"] = Relationship(back_populates="shipping_address")


class SellerProfile(SQLModel, table=True):
    __tablename__ = "seller_profiles"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", unique=True)
    store_name: str = Field(max_length=200)
    store_description: Optional[str] = Field(default=None, max_length=1000)
    store_logo_url: Optional[str] = Field(default=None, max_length=500)
    business_license: Optional[str] = Field(default=None, max_length=100)
    is_verified: bool = Field(default=False)
    rating: Decimal = Field(default=Decimal("0.0"), max_digits=3, decimal_places=2)
    total_sales: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    user: User = Relationship(back_populates="seller_profile")


class Category(SQLModel, table=True):
    __tablename__ = "categories"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100, unique=True)
    description: Optional[str] = Field(default=None, max_length=500)
    parent_id: Optional[int] = Field(default=None, foreign_key="categories.id")
    image_url: Optional[str] = Field(default=None, max_length=500)
    is_active: bool = Field(default=True)
    sort_order: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    parent: Optional["Category"] = Relationship(
        back_populates="children", sa_relationship_kwargs={"remote_side": "Category.id"}
    )
    children: List["Category"] = Relationship(back_populates="parent")
    products: List["Product"] = Relationship(back_populates="category")


class Product(SQLModel, table=True):
    __tablename__ = "products"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    seller_id: int = Field(foreign_key="users.id")
    category_id: int = Field(foreign_key="categories.id")
    name: str = Field(max_length=200)
    description: str = Field(max_length=2000)
    price: Decimal = Field(max_digits=12, decimal_places=2)
    original_price: Optional[Decimal] = Field(default=None, max_digits=12, decimal_places=2)
    stock_quantity: int = Field(default=0)
    min_order_quantity: int = Field(default=1)
    weight_kg: Decimal = Field(max_digits=8, decimal_places=3)  # For shipping calculations
    dimensions: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))  # length, width, height in cm
    images: List[str] = Field(default=[], sa_column=Column(JSON))  # List of image URLs
    specifications: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    tags: List[str] = Field(default=[], sa_column=Column(JSON))
    is_active: bool = Field(default=True)
    is_featured: bool = Field(default=False)
    rating: Decimal = Field(default=Decimal("0.0"), max_digits=3, decimal_places=2)
    total_reviews: int = Field(default=0)
    total_sold: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    seller: User = Relationship(back_populates="products")
    category: Category = Relationship(back_populates="products")
    cart_items: List["CartItem"] = Relationship(back_populates="product")
    order_items: List["OrderItem"] = Relationship(back_populates="product")
    reviews: List["ProductReview"] = Relationship(back_populates="product")


class CartItem(SQLModel, table=True):
    __tablename__ = "cart_items"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    product_id: int = Field(foreign_key="products.id")
    quantity: int = Field(default=1)
    added_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    user: User = Relationship(back_populates="cart_items")
    product: Product = Relationship(back_populates="cart_items")


class Order(SQLModel, table=True):
    __tablename__ = "orders"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    shipping_address_id: int = Field(foreign_key="addresses.id")
    order_number: str = Field(unique=True, max_length=50)
    status: OrderStatus = Field(default=OrderStatus.PENDING)
    subtotal: Decimal = Field(max_digits=12, decimal_places=2)
    shipping_fee: Decimal = Field(default=Decimal("0.00"), max_digits=12, decimal_places=2)
    tax_amount: Decimal = Field(default=Decimal("0.00"), max_digits=12, decimal_places=2)
    discount_amount: Decimal = Field(default=Decimal("0.00"), max_digits=12, decimal_places=2)
    total_amount: Decimal = Field(max_digits=12, decimal_places=2)
    payment_method: str = Field(max_length=50)
    payment_status: str = Field(default="pending", max_length=20)
    notes: Optional[str] = Field(default=None, max_length=500)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    user: User = Relationship(back_populates="orders")
    shipping_address: Address = Relationship(back_populates="orders")
    order_items: List["OrderItem"] = Relationship(back_populates="order")
    delivery: Optional["Delivery"] = Relationship(back_populates="order")


class OrderItem(SQLModel, table=True):
    __tablename__ = "order_items"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="orders.id")
    product_id: int = Field(foreign_key="products.id")
    quantity: int
    unit_price: Decimal = Field(max_digits=12, decimal_places=2)
    total_price: Decimal = Field(max_digits=12, decimal_places=2)
    seller_id: int = Field(foreign_key="users.id")  # For seller order management

    # Relationships
    order: Order = Relationship(back_populates="order_items")
    product: Product = Relationship(back_populates="order_items")
    seller: User = Relationship()


class Delivery(SQLModel, table=True):
    __tablename__ = "deliveries"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="orders.id", unique=True)
    komerce_delivery_id: Optional[str] = Field(default=None, max_length=100)  # ID from Komerce API
    courier_name: str = Field(max_length=100)
    courier_phone: Optional[str] = Field(default=None, max_length=20)
    tracking_number: Optional[str] = Field(default=None, max_length=100)
    status: DeliveryStatus = Field(default=DeliveryStatus.PENDING)
    estimated_delivery: Optional[datetime] = Field(default=None)
    actual_delivery: Optional[datetime] = Field(default=None)
    pickup_address: str = Field(max_length=500)
    delivery_address: str = Field(max_length=500)
    delivery_fee: Decimal = Field(max_digits=10, decimal_places=2)
    insurance_fee: Decimal = Field(default=Decimal("0.00"), max_digits=10, decimal_places=2)
    delivery_notes: Optional[str] = Field(default=None, max_length=500)
    komerce_response: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))  # Store API response
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    order: Order = Relationship(back_populates="delivery")


class ProductReview(SQLModel, table=True):
    __tablename__ = "product_reviews"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="products.id")
    user_id: int = Field(foreign_key="users.id")
    order_item_id: Optional[int] = Field(default=None, foreign_key="order_items.id")  # Link to purchase
    rating: int = Field(ge=1, le=5)
    title: Optional[str] = Field(default=None, max_length=200)
    comment: Optional[str] = Field(default=None, max_length=1000)
    images: List[str] = Field(default=[], sa_column=Column(JSON))  # Review images
    is_verified_purchase: bool = Field(default=False)
    helpful_count: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    product: Product = Relationship(back_populates="reviews")
    user: User = Relationship()
    order_item: Optional[OrderItem] = Relationship()


# Non-persistent schemas (for validation, forms, API requests/responses)
class UserCreate(SQLModel, table=False):
    email: str = Field(max_length=255, regex=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
    password: str = Field(min_length=8, max_length=100)
    full_name: str = Field(max_length=100)
    phone: Optional[str] = Field(default=None, max_length=20)
    role: UserRole = Field(default=UserRole.BUYER)


class UserUpdate(SQLModel, table=False):
    full_name: Optional[str] = Field(default=None, max_length=100)
    phone: Optional[str] = Field(default=None, max_length=20)


class AddressCreate(SQLModel, table=False):
    label: str = Field(max_length=50)
    full_address: str = Field(max_length=500)
    city: str = Field(max_length=100)
    state: str = Field(max_length=100)
    postal_code: str = Field(max_length=20)
    country: str = Field(max_length=100, default="Indonesia")
    is_default: bool = Field(default=False)


class SellerProfileCreate(SQLModel, table=False):
    store_name: str = Field(max_length=200)
    store_description: Optional[str] = Field(default=None, max_length=1000)
    store_logo_url: Optional[str] = Field(default=None, max_length=500)
    business_license: Optional[str] = Field(default=None, max_length=100)


class ProductCreate(SQLModel, table=False):
    category_id: int
    name: str = Field(max_length=200)
    description: str = Field(max_length=2000)
    price: Decimal = Field(max_digits=12, decimal_places=2)
    original_price: Optional[Decimal] = Field(default=None, max_digits=12, decimal_places=2)
    stock_quantity: int = Field(default=0)
    min_order_quantity: int = Field(default=1)
    weight_kg: Decimal = Field(max_digits=8, decimal_places=3)
    dimensions: Dict[str, Any] = Field(default={})
    images: List[str] = Field(default=[])
    specifications: Dict[str, Any] = Field(default={})
    tags: List[str] = Field(default=[])


class ProductUpdate(SQLModel, table=False):
    name: Optional[str] = Field(default=None, max_length=200)
    description: Optional[str] = Field(default=None, max_length=2000)
    price: Optional[Decimal] = Field(default=None, max_digits=12, decimal_places=2)
    original_price: Optional[Decimal] = Field(default=None, max_digits=12, decimal_places=2)
    stock_quantity: Optional[int] = Field(default=None)
    weight_kg: Optional[Decimal] = Field(default=None, max_digits=8, decimal_places=3)
    dimensions: Optional[Dict[str, Any]] = Field(default=None)
    images: Optional[List[str]] = Field(default=None)
    specifications: Optional[Dict[str, Any]] = Field(default=None)
    tags: Optional[List[str]] = Field(default=None)
    is_active: Optional[bool] = Field(default=None)


class CartItemCreate(SQLModel, table=False):
    product_id: int
    quantity: int = Field(default=1, ge=1)


class CartItemUpdate(SQLModel, table=False):
    quantity: int = Field(ge=1)


class OrderCreate(SQLModel, table=False):
    shipping_address_id: int
    payment_method: str = Field(max_length=50)
    notes: Optional[str] = Field(default=None, max_length=500)


class DeliveryCreate(SQLModel, table=False):
    courier_name: str = Field(max_length=100)
    pickup_address: str = Field(max_length=500)
    delivery_address: str = Field(max_length=500)
    delivery_fee: Decimal = Field(max_digits=10, decimal_places=2)
    insurance_fee: Decimal = Field(default=Decimal("0.00"), max_digits=10, decimal_places=2)
    delivery_notes: Optional[str] = Field(default=None, max_length=500)


class ProductReviewCreate(SQLModel, table=False):
    rating: int = Field(ge=1, le=5)
    title: Optional[str] = Field(default=None, max_length=200)
    comment: Optional[str] = Field(default=None, max_length=1000)
    images: List[str] = Field(default=[])
