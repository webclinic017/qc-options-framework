#region imports
from AlgorithmImports import *
#endregion

from .Base import Base


class HedgeRiskManagementModel(Base):
    def __init__(self, context):
        # Call the Base class __init__ method
        super().__init__(context)
