"""FPL Main region data collection api client"""

import json
import logging
from datetime import datetime
import aiohttp
import async_timeout


from .const import (
    API_HOST,
    LOGIN_RESULT_FAILURE,
    LOGIN_RESULT_INVALIDPASSWORD,
    LOGIN_RESULT_INVALIDUSER,
    LOGIN_RESULT_OK,
    TIMEOUT,
)

STATUS_CATEGORY_OPEN = "OPEN"

# URL_LOGIN = API_HOST + "/api/resources/login"
URL_LOGIN = (
    API_HOST
    + "/cs/customer/v1/registration/loginAndUseMigration?migrationToggle=Y&view=LoginMini"
)

URL_BUDGET_BILLING_GRAPH = (
    API_HOST + "/api/resources/account/{account}/budgetBillingGraph"
)

URL_RESOURCES_PROJECTED_BILL = (
    API_HOST
    + "/api/resources/account/{account}/projectedBill"
    + "?premiseNumber={premise}&lastBilledDate={lastBillDate}"
)


URL_BUDGET_BILLING_PREMISE_DETAILS = (
    API_HOST + "/api/resources/account/{account}/budgetBillingGraph/premiseDetails"
)


ENROLLED = "ENROLLED"
NOTENROLLED = "NOTENROLLED"

_LOGGER = logging.getLogger(__package__)


class FplMainRegionApiClient:
    """Fpl Main Region Api Client"""

    def __init__(self, username, password, loop, session) -> None:
        self.session = session
        self.username = username
        self.password = password
        self.loop = loop

    async def login(self):
        """login into fpl"""

        # login and get account information

        async with async_timeout.timeout(TIMEOUT):
            response = await self.session.get(
                URL_LOGIN,
                auth=aiohttp.BasicAuth(self.username, self.password),
            )

        if response.status == 200:
            # Get JWT token from headers if present
            jwt_token = response.headers.get("jwttoken")
            if jwt_token:
                self.jwt_token = jwt_token  # Store in a property
            return LOGIN_RESULT_OK

        if response.status == 401:
            json_data = json.loads(await response.text())

            if json_data["messageCode"] == LOGIN_RESULT_INVALIDUSER:
                return LOGIN_RESULT_INVALIDUSER

            if json_data["messageCode"] == LOGIN_RESULT_INVALIDPASSWORD:
                return LOGIN_RESULT_INVALIDPASSWORD

        return LOGIN_RESULT_FAILURE

    async def get_open_accounts(self):
        """
        Get open accounts

        Returns array with active account numbers
        """
        result = []
        URL = API_HOST + "/api/resources/header"
        headers = {}
        if hasattr(self, "jwt_token") and self.jwt_token:
            headers["jwttoken"] = self.jwt_token

        async with async_timeout.timeout(TIMEOUT):
            response = await self.session.get(URL, headers=headers)

        json_data = await response.json()
        accounts = json_data["data"]["accounts"]["data"]["data"]

        for account in accounts:
            if account["statusCategory"] == STATUS_CATEGORY_OPEN:
                result.append(account["accountNumber"])

        return result

    async def logout(self):
        """Logging out from fpl"""
        _LOGGER.info("Logging out")

        URL_LOGOUT = API_HOST + "/api/resources/logout"
        try:
            async with async_timeout.timeout(TIMEOUT):
                await self.session.get(URL_LOGOUT)
        except Exception as e:
            _LOGGER.error(e)

    async def update(self, account) -> dict:
        """Get data from resources endpoint"""
        data = {}

        URL_RESOURCES_ACCOUNT = API_HOST + "/api/resources/account/{account}"
        headers = {}
        if hasattr(self, "jwt_token") and self.jwt_token:
            headers["jwttoken"] = self.jwt_token
        async with async_timeout.timeout(TIMEOUT):
            response = await self.session.get(
                URL_RESOURCES_ACCOUNT.format(account=account), headers=headers
            )
        account_data = (await response.json())["data"]

        premise = account_data.get("premiseNumber").zfill(9)

        data["meterSerialNo"] = account_data["meterSerialNo"]
        # data["meterNo"] = account_data["meterNo"]
        meterno = account_data["meterNo"]

        # currentBillDate
        currentBillDate = datetime.strptime(
            account_data["currentBillDate"].replace("-", "").split("T")[0], "%Y%m%d"
        ).date()

        # nextBillDate
        nextBillDate = datetime.strptime(
            account_data["nextBillDate"].replace("-", "").split("T")[0], "%Y%m%d"
        ).date()

        data["current_bill_date"] = str(currentBillDate)
        data["next_bill_date"] = str(nextBillDate)

        today = datetime.now().date()

        data["service_days"] = (nextBillDate - currentBillDate).days
        data["as_of_days"] = (today - currentBillDate).days
        data["remaining_days"] = (nextBillDate - today).days

        # zip code
        # zip_code = accountData["serviceAddress"]["zip"]

        # projected bill
        pbData = await self.__getFromProjectedBill(account, premise, currentBillDate)
        data.update(pbData)

        # programs
        programsData = account_data["programs"]["data"]

        programs = dict()
        _LOGGER.info("Getting Programs")
        for program in programsData:
            if "enrollmentStatus" in program.keys():
                key = program["name"]
                programs[key] = program["enrollmentStatus"] == ENROLLED

        def hasProgram(programName) -> bool:
            return programName in programs and programs[programName]

        # Budget Billing program
        if hasProgram("BBL"):
            data["budget_bill"] = True
            bbl_data = await self.__getBBL_async(account, data)
            data.update(bbl_data)
        else:
            data["budget_bill"] = False

        # Get data from energy service
        data.update(
            await self.__getDataFromEnergyServiceDaily(
                account, premise, currentBillDate, meterno
            )
        )

        data.update(
            await self.__getDataFromEnergyService(
                account, premise, currentBillDate, meterno
            )
        )

        # Get data from energy service ( hourly )
        # data.update(await self.__getDataFromEnergyServiceHourly(account, premise, meterno))

        # data.update(await self.__getDataFromApplianceUsage(account, currentBillDate))

        # Gets the account balance and past due status.
        data.update(await self.get_account_details(account))

        return data

    async def __getFromProjectedBill(self, account, premise, currentBillDate) -> dict:
        """get data from projected bill endpoint"""
        data = {}

        try:
            headers = {}
            if hasattr(self, "jwt_token") and self.jwt_token:
                headers["jwttoken"] = self.jwt_token
            async with async_timeout.timeout(TIMEOUT):
                response = await self.session.get(
                    URL_RESOURCES_PROJECTED_BILL.format(
                        account=account,
                        premise=premise,
                        lastBillDate=currentBillDate.strftime("%m%d%Y"),
                    ),
                    headers=headers,
                )

            if response.status == 200:
                projectedBillData = (await response.json())["data"]

                billToDate = float(projectedBillData["billToDate"])
                projectedBill = float(projectedBillData["projectedBill"])
                dailyAvg = float(projectedBillData["dailyAvg"])
                avgHighTemp = int(projectedBillData["avgHighTemp"])

                data["bill_to_date"] = billToDate
                data["projected_bill"] = projectedBill
                data["daily_avg"] = dailyAvg
                data["avg_high_temp"] = avgHighTemp

        except Exception as e:
            _LOGGER.error(e)

        return data

    async def __getBBL_async(self, account, projectedBillData) -> dict:
        """Get budget billing data"""
        _LOGGER.info("Getting budget billing data")
        data = {}

        try:
            headers = {}
            if hasattr(self, "jwt_token") and self.jwt_token:
                headers["jwttoken"] = self.jwt_token
            async with async_timeout.timeout(TIMEOUT):
                response = await self.session.get(
                    URL_BUDGET_BILLING_PREMISE_DETAILS.format(account=account),
                    headers=headers,
                )
                if response.status == 200:
                    r = (await response.json())["data"]
                    dataList = r["graphData"]

                    # startIndex = len(dataList) - 1

                    billingCharge = 0
                    budgetBillDeferBalance = r["defAmt"]

                    projectedBill = projectedBillData["projected_bill"]
                    asOfDays = projectedBillData["as_of_days"]

                    for det in dataList:
                        billingCharge += det["actuallBillAmt"]

                    calc1 = (projectedBill + billingCharge) / 12
                    calc2 = (1 / 12) * (budgetBillDeferBalance)

                    projectedBudgetBill = round(calc1 + calc2, 2)
                    bbDailyAvg = round(projectedBudgetBill / 30, 2)
                    bbAsOfDateAmt = round(projectedBudgetBill / 30 * asOfDays, 2)

                    data["budget_billing_daily_avg"] = bbDailyAvg
                    data["budget_billing_bill_to_date"] = bbAsOfDateAmt

                    data["budget_billing_projected_bill"] = float(projectedBudgetBill)

            headers = {}
            if hasattr(self, "jwt_token") and self.jwt_token:
                headers["jwttoken"] = self.jwt_token
            async with async_timeout.timeout(TIMEOUT):
                response = await self.session.get(
                    URL_BUDGET_BILLING_GRAPH.format(account=account), headers=headers
                )
                if response.status == 200:
                    r = (await response.json())["data"]
                    data["bill_to_date"] = float(r["eleAmt"])
                    data["defered_amount"] = float(r["defAmt"])
        except Exception as e:
            _LOGGER.error(e)

        return data

    async def __getDataFromEnergyServiceDaily(
        self, account, premise, lastBilledDate, meterno
    ) -> dict:
        _LOGGER.info("Getting energy service data: Daily")

        date = str(lastBilledDate.strftime("%m%d%Y"))
        json = {
            "accountType": "RESIDENTIAL",
            "amrFlag": "Y",
            "applicationPage": "resDashBoard",
            "billComparisionFlag": False,
            "channel": "WEB",
            "endDate": "",
            "frequencyType": "Daily",
            "lastBilledDate": date,
            "meterNo": meterno,
            "monthlyFlag": False,
            "premiseNumber": premise,
            "projectedBillFlag": False,
            "revCode": "1",
            "startDate": "",
            "status": 2,
        }
        URL_ENERGY_SERVICE = (
            API_HOST
            # + "/dashboard-api/resources/account/{account}/energyService/{account}"
            + "/cs/customer/v1/energydashboard/resources/account/{account}/res-energy-service"
        )

        data = {}
        try:
            headers = {}
            if hasattr(self, "jwt_token") and self.jwt_token:
                headers["jwttoken"] = self.jwt_token
            async with async_timeout.timeout(TIMEOUT):
                response = await self.session.post(
                    URL_ENERGY_SERVICE.format(account=account),
                    json=json,
                    headers=headers,
                )
                if response.status == 200:
                    rd = await response.json()
                    if "data" not in rd.keys():
                        return {}

                    r = rd["data"]
                    dailyUsage = []

                    # totalPowerUsage = 0
                    if "DailyUsage" in r and "data" in r["DailyUsage"]:
                        dailyData = rd["data"]["DailyUsage"]["data"]
                        for daily in dailyData:
                            if daily["missingDay"] != "true":
                                dailyUsage.append(
                                    {
                                        "usage": daily["kwhUsed"]
                                        if "kwhUsed" in daily.keys()
                                        else None,
                                        "cost": daily["billingCharge"]
                                        if "billingCharge" in daily.keys()
                                        else None,
                                        # "date": daily["date"],
                                        "max_temperature": daily[
                                            "averageHighTemperature"
                                        ]
                                        if "averageHighTemperature" in daily.keys()
                                        else None,
                                        "netDeliveredKwh": daily["netDeliveredKwh"]
                                        if "netDeliveredKwh" in daily.keys()
                                        else 0,
                                        "netReceivedKwh": daily["netReceivedKwh"]
                                        if "netReceivedKwh" in daily.keys()
                                        else 0,
                                        "netDeliveredReading": daily[
                                            "netDeliveredReading"
                                        ]
                                        if "netDeliveredReading" in daily.keys()
                                        else 0,
                                        "netReceivedReading": daily[
                                            "netReceivedReading"
                                        ]
                                        if "netReceivedReading" in daily.keys()
                                        else 0,
                                        "readTime": datetime.fromisoformat(
                                            daily[
                                                "readTime"
                                            ]  # 2022-02-25T00:00:00.000-05:00
                                        ),
                                    }
                                )
                            # totalPowerUsage += int(daily["kwhUsed"])

                        # data["total_power_usage"] = totalPowerUsage
                        data["daily_usage"] = dailyUsage
        except Exception as e:
            _LOGGER.error(e)

        return data

    async def __getDataFromEnergyService(
        self, account, premise, lastBilledDate, meterno
    ) -> dict:
        _LOGGER.info("Getting energy service data")

        # Tested using MITM proxy and iOS app. 
        # This is the payload and url used by the iOS app.
        json = {
            "status": "2",
            "accountType": "RESIDENTIAL",
            "premiseNumber": premise,
            "lastBilledDate": lastBilledDate.strftime("%m%d%Y"),
            "amrFlag": "Y",
            "revCode": "1",
            "meterNo": meterno
        }
        URL_ENERGY_SERVICE = (
            API_HOST
            + "/cs/customer/v1/energydashboard/resources/energy-usage/account/{account}/mobile-energy-service"
        )

        data = {}
        try:
            headers = {}
            if hasattr(self, "jwt_token") and self.jwt_token:
                headers["jwttoken"] = self.jwt_token
            async with async_timeout.timeout(TIMEOUT):
                response = await self.session.post(
                    URL_ENERGY_SERVICE.format(account=account),
                    json=json,
                    headers=headers,
                )
                if response.status == 200:
                    response_data = await response.json()
                    json_data = response_data["data"]
                    
                    current_usage = json_data["CurrentUsage"]
                    data["projectedKWH"] = int(current_usage.get("projectedKWH"))
                    data["dailyAverageKWH"] = float(current_usage.get("dailyAverageKWH"))
                    data["billToDateKWH"] = float(current_usage.get("billToDateKWH"))
                    data["recMtrReading"] = int(current_usage.get("recMtrReading") or 0)
                    data["delMtrReading"] = int(current_usage.get("delMtrReading") or 0)
                    data["billStartDate"] = datetime.strptime(current_usage.get("billStartDate"), "%m-%d-%Y").date()
                    data["billEndDate"] = datetime.strptime(current_usage.get("billEndDate"), "%m-%d-%Y").date()

                    daily_usage = json_data["DailyUsage"]
                    last_day_usage = daily_usage["endDate"]

                    data["DailyUsage"] = {}
                    for day_usage in daily_usage["data"]:
                        # We want to get the last day's usage and use that as the sensor information.
                        # Given that this sensor should reset every day to the previous day's usage.
                        if day_usage["date"] == last_day_usage:
                            data["DailyUsage"]["kwhActual"] = float(day_usage.get("kwhActual") or 0)
                            data["DailyUsage"]["billingCharge"] = float(day_usage.get("billingCharge") or 0)
                            data["DailyUsage"]["readTime"] = datetime.fromisoformat(day_usage.get("readTime"))
                            data["DailyUsage"]["reading"] = float(day_usage.get("reading"))

                    data["HourlyUsage"] = {}

        except Exception as e:
            _LOGGER.error(e)

        return data

    async def __getDataFromEnergyServiceHourly(self, account, premise, meterno) -> dict:
        _LOGGER.info("Getting energy service hourly data")

        today = str(datetime.now().strftime("%m%d%Y"))
        JSON = {
            "status": 2,
            "channel": "WEB",
            "amrFlag": "Y",
            "accountType": "RESIDENTIAL",
            "revCode": "1",
            "premiseNumber": premise,
            "meterNo": meterno,
            "projectedBillFlag": False,
            "billComparisionFlag": False,
            "monthlyFlag": False,
            "frequencyType": "Hourly",
            "applicationPage": "resDashBoard",
            "startDate": today,
            "endDate": "",
        }

        URL_ENERGY_SERVICE = (
            API_HOST
            + "/dashboard-api/resources/account/{account}/energyService/{account}"
        )

        data = {}
        try:
            async with async_timeout.timeout(TIMEOUT):
                response = await self.session.post(
                    URL_ENERGY_SERVICE.format(account=account), json=JSON
                )
                if response.status == 200:
                    rd = await response.json()
                    if "data" not in rd.keys():
                        return {}

                    hourlyUsage = []

                    # totalPowerUsage = 0
                    if (
                        "data" in rd.keys()
                        and "HourlyUsage" in rd["data"]
                        and "data" in rd["data"]["HourlyUsage"]
                    ):
                        hourlyData = rd["data"]["HourlyUsage"]["data"]
                        for hourly in hourlyData:
                            hourlyUsage.append(
                                {
                                    "usage": hourly["kwhUsed"]
                                    if "kwhUsed" in hourly.keys()
                                    else None,
                                    "cost": hourly["billingCharged"]
                                    if "billingCharged" in hourly.keys()
                                    else None,
                                    "temperature": hourly["temperature"]
                                    if "temperature" in hourly.keys()
                                    else None,
                                    "netDelivered": hourly["netDelivered"]
                                    if "netDelivered" in hourly.keys()
                                    else 0,
                                    "netReceived": hourly["netReceived"]
                                    if "netReceived" in hourly.keys()
                                    else 0,
                                    "reading": hourly["reading"]
                                    if "reading" in hourly.keys()
                                    else 0,
                                    "kwhActual": hourly["kwhActual"]
                                    if "kwhActual" in hourly.keys()
                                    else 0,
                                    "readTime": datetime.fromisoformat(
                                        hourly[
                                            "readTime"
                                        ]  # 2022-02-25T00:00:00.000-05:00
                                    ),
                                }
                            )

                        data["hourly_usage"] = hourlyUsage
        except Exception as e:
            _LOGGER.error(e)

        return data

    async def __getDataFromApplianceUsage(self, account, lastBilledDate) -> dict:
        """get data from appliance usage"""
        _LOGGER.info("Getting appliance usage data")

        URL_APPLIANCE_USAGE = (
            API_HOST
            + "/dashboard-api/resources/account/{account}/applianceUsage/{account}"
        )

        JSON = {"startDate": str(lastBilledDate.strftime("%m%d%Y"))}
        data = {}

        try:
            headers = {}
            if hasattr(self, "jwt_token") and self.jwt_token:
                headers["jwttoken"] = self.jwt_token
            async with async_timeout.timeout(TIMEOUT):
                response = await self.session.post(
                    URL_APPLIANCE_USAGE.format(account=account),
                    json=JSON,
                    headers=headers,
                )
                if response.status == 200:
                    data = (await response.json())["data"]
                    if "electric" in data:
                        electric = data["electric"]

                        full = 100
                        for e in electric:
                            rr = round(float(e["percentageDollar"]))
                            if rr < full:
                                full = full - rr
                            else:
                                rr = full
                            data[e["category"].replace(" ", "_")] = rr
                    else:
                        _LOGGER.info("appliance usage data does not exist")
        except Exception as e:
            _LOGGER.error(e)

        return {"energy_percent_by_applicance": data}

    async def get_account_details(self, account_number: str) -> dict:
        """Get accounts"""

        _LOGGER.info("Getting accounts")

        data = {}

        ACCOUNTS_URL = API_HOST + "/cs/customer/v1/multiaccount/resources/userId/current/accounts?contactFlag=N&count=5&view=profileAccountsList"

        try:
            headers = {}
            if hasattr(self, "jwt_token") and self.jwt_token:
                headers["jwttoken"] = self.jwt_token
            async with async_timeout.timeout(TIMEOUT):
                response = await self.session.get(ACCOUNTS_URL, headers=headers)
                if response.status == 200:
                    json_data = await response.json()
                    data = json_data["data"]

                    for account in data["data"]:
                        if account["accountNumber"] == account_number:
                            return account

                    data["balance"] = float(account["balance"])
                    data["pastDue"] = bool(account["pastDue"])
                    # There a more fields available in the response, but none that seem to be useful.
                    # For example, deposit, statusCategory (ex, OPEN, CLOSED), and property address.
                    
        except Exception as e:
            _LOGGER.error(e)

        return data
