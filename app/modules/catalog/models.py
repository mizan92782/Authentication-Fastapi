from tortoise import fields
from app.shared.base.base_model import BaseModel


class Category(BaseModel):
    name = fields.CharField(max_length=100, unique=True)
    slug = fields.CharField(max_length=120, unique=True)
    description = fields.TextField(null=True)
    image = fields.CharField(max_length=500, null=True)

    class Meta:
        table = "categories"

    def __str__(self):
        return self.name


class Product(BaseModel):
    category = fields.ForeignKeyField("models.Category", related_name="products", on_delete=fields.CASCADE)
    name = fields.CharField(max_length=200)
    slug = fields.CharField(max_length=220, unique=True)
    description = fields.TextField(null=True)
    price = fields.DecimalField(max_digits=12, decimal_places=2)
    compare_price = fields.DecimalField(max_digits=12, decimal_places=2, null=True)
    stock = fields.IntField(default=0)
    sku = fields.CharField(max_length=100, unique=True)
    is_active = fields.BooleanField(default=True)

    class Meta:
        table = "products"

    def __str__(self):
        return self.name


class ProductImage(BaseModel):
    product = fields.ForeignKeyField("models.Product", related_name="images", on_delete=fields.CASCADE)
    url = fields.CharField(max_length=500)
    alt = fields.CharField(max_length=200, null=True)
    is_primary = fields.BooleanField(default=False)

    class Meta:
        table = "product_images"
