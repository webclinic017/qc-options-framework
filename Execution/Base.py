from AlgorithmImports import *

from Tools import ContractUtils, Logger
from Execution.Utils import MarketOrderHandler, LimitOrderHandler
"""
"""

class Base(ExecutionModel):
    DEFAULT_PARAMETERS = {
        # Retry decrease/increase percentage. Each time we try and get a fill we are going to decrease the limit price
        # by this percentage.
        "retryChangePct": 1.0,
        # Minimum price percentage accepted as limit price. If the limit price set is 0.5 and this value is 0.8 then
        # the minimum price accepted will be 0.4
        "minPricePct": 0.7,
        # The limit order price initial adjustmnet. This will add some leeway to the limit order price so we can try and get
        # some more favorable price for the user than the algo set price. So if we set this to 0.1 (10%) and our limit price
        # is 0.5 then we will try and fill the order at 0.55 first.
        "orderAdjustmentPct": -0.2,
        # The increment we are going to use to adjust the limit price. This is used to 
        # properly adjust the price for SPX options. If the limit price is 0.5 and this
        # value is 0.01 then we are going to try and fill the order at 0.51, 0.52, 0.53, etc.
        "adjustmentIncrement": None, # 0.01,
        # Speed of fill. Option taken from https://optionalpha.com/blog/smartpricing-released. 
        # Can be: "Normal", "Fast", "Patient"
        # "Normal" will retry every 3 minutes, "Fast" every 1 minute, "Patient" every 5 minutes.
        "speedOfFill": "Fast",
        # maxRetries is the maximum number of retries we are going to do to try 
        # and get a fill. This is calculated based on the speedOfFill and this 
        # value is just for reference.
        "maxRetries": 10,
    }

    def __init__(self, context):
        self.context = context

        # Calculate maxRetries based on speedOfFill
        speedOfFill = self.parameter("speedOfFill")
        if speedOfFill == "Patient":
            self.maxRetries = 7
        elif speedOfFill == "Normal":
            self.maxRetries = 5
        elif speedOfFill == "Fast":
            self.maxRetries = 3
        else:
            raise ValueError("Invalid speedOfFill value")

        self.targetsCollection = PortfolioTargetCollection()
        self.contractUtils = ContractUtils(context)
        # Set the logger
        self.logger = Logger(context, className=type(self).__name__, logLevel=context.logLevel)
        self.marketOrderHandler = MarketOrderHandler(context, self)
        self.limitOrderHandler = LimitOrderHandler(context, self)

        # Gets or sets the maximum spread compare to current price in percentage.
        # self.acceptingSpreadPercent = Math.Abs(acceptingSpreadPercent)
        # self.executionTimeThreshold = timedelta(minutes=10)
        # self.openExecutedOrders = {}

        self.context.structure.AddConfiguration(parent=self, **self.getMergedParameters())

    @classmethod
    def getMergedParameters(cls):
        # Merge the DEFAULT_PARAMETERS from both classes
        return {**cls.DEFAULT_PARAMETERS, **getattr(cls, "PARAMETERS", {})}

    @classmethod
    def parameter(cls, key, default=None):
        return cls.getMergedParameters().get(key, default)

    def Execute(self, algorithm, targets):
        self.context.executionTimer.start('Execution.Base -> Execute')

        # Use this section to check if a target is in the workingOrder dict
        self.targetsCollection.AddRange(targets)

        # Check if the workingOrders are still OK to execute
        self.context.structure.checkOpenPositions()

        for order in list(self.context.workingOrders.values()):
            position = self.context.allPositions[order.orderId]

            useLimitOrders = order.useLimitOrder
            useMarketOrders = not useLimitOrders

            if useMarketOrders:
                self.marketOrderHandler.call(position, order)
            elif useLimitOrders:
                self.limitOrderHandler.call(position, order)

        # if not self.targetsCollection.IsEmpty:
        #     for target in targets:
        #         order = Helper().findIn(
        #             self.context.workingOrders.values(),
        #             lambda v: any(t == target for t in v.targets)
        #         )
        #         orders[order.orderId] = order

        #     for order in orders.values():
        #         position = self.context.allPositions[order.orderId]
        #         useLimitOrders = order.useLimitOrder
        #         useMarketOrders = not useLimitOrders

        #         if useMarketOrders:
        #             self.executeMarketOrder(position, order)
        #         elif useLimitOrders:
        #             self.executeLimitOrder(position, order)

        self.targetsCollection.ClearFulfilled(algorithm)
        # Update the charts after execution
        self.context.charting.updateCharts()

        self.context.executionTimer.stop('Execution.Base -> Execute')


