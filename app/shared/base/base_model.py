import uuid
from tortoise import fields
from tortoise.models import Model


#=================== Base MOdel ============

class BaseModel(Model):
    id =fields.UUIDField(pk=True,default=uuid.uuid4,editable=False)
    created_at = fields.DatetimeField( auto_new_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    is_deleted=fields.BooleanField(default=False,index=True)
    

    class Meta:
        abstract=True
        ordering = ['id']

    async def soft_delete(self)->None:
        self.is_deleted=True
        await self.save(
            update_fields=[
                'is_deleted',
                'updated_at'
            ]
        )

    
    async def restore(self)->None:
        self.is_deleted=False
        await self.save(
            update_fields=[
                'is_deleted',
                'updated_at'
            ]
        )


    @classmethod
    def active(cls):
        "Return only  non-deleted records"
        return cls.filter(is_deleted=False)
    





'''
============== index ================
User.objects.filter(is_deleted=False)

# Without index
ID   Name   is_deleted
----------------------
1    A      False
2    B      True
3    C      False
4    D      True
5    E      False


with index

INDEX on is_deleted
------------------------

False → [1, 3, 5]
True  → [2, 4]





===================== Time =========
auto_new_add  : Afte assing can not change
auto_now : Update when updata value





==================== Meta class  ===========

if define the model configurations
Model = data structure
Meta = model-এর rules/settings



======================= abstract===============
abstract = True : its not create table in database



===================== Fieils update ===============

Not update all fields ,only update thest fiels
 update_fields=[
                'is_deleted',
                'updated_at'
            ]
'''