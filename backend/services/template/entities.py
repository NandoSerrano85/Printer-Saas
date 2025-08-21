from sqlalchemy import Column, Float, Integer, String, Boolean, DateTime, func, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from common.database import Base

class EtsyProductTemplate(Base):
    __tablename__ = 'etsy_product_templates'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String, nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    name = Column(String, nullable=False)
    template_title = Column(String, nullable=True)
    title = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    who_made = Column(String, nullable=True)
    when_made = Column(String, nullable=True)
    taxonomy_id = Column(Integer, nullable=True)
    price = Column(Float, nullable=True)
    materials = Column(Text, nullable=True)
    shop_section_id = Column(Integer, nullable=True)
    quantity = Column(Integer, nullable=True)
    tags = Column(Text, nullable=True)
    item_weight = Column(Float, nullable=True)
    item_weight_unit = Column(String, nullable=True)
    item_length = Column(Float, nullable=True)
    item_width = Column(Float, nullable=True)
    item_height = Column(Float, nullable=True)
    item_dimensions_unit = Column(String, nullable=True)
    is_taxable = Column(Boolean, nullable=True)
    type = Column(String, nullable=True)
    processing_min = Column(Integer, nullable=True)
    processing_max = Column(Integer, nullable=True)
    return_policy_id = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = ({'schema': 'templates'},)