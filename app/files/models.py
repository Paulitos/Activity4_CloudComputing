from tortoise.models import Model
from tortoise import fields


class File(Model):
    id = fields.IntField(pk=True)
    file_id = fields.CharField(max_length=36, unique=True)  # UUID string
    name = fields.CharField(max_length=255)
    description = fields.TextField(null=True)
    amount_of_pages = fields.IntField()
    file_path = fields.CharField(max_length=500, null=True)
    owner = fields.ForeignKeyField("authentication.User", related_name="files")
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    is_uploaded = fields.BooleanField(default=False)
    
    class Meta:
        table = "files"
    
    def to_dict(self):
        """Convert file to dictionary for API responses"""
        return {
            "file_id": self.file_id,
            "name": self.name,
            "description": self.description,
            "pages": self.amount_of_pages,
            "uploaded": self.is_uploaded,
            "created_at": str(self.created_at),
            "updated_at": str(self.updated_at)
        }