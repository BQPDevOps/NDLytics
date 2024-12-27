import requests
from typing import Optional, Dict, Any, List, Union
from datetime import datetime


class TCNClient:
    """Client for interacting with the TCN Platform 3.0 API"""

    def __init__(
        self, access_token: str, base_url: str = "https://api.tcnp3.com/backoffice/"
    ):
        """
        Initialize TCN API client

        Args:
            access_token: API access token for authentication
            base_url: Base URL for API endpoints. Defaults to US region
        """
        self.access_token = access_token
        self.base_url = base_url

    def create_contacts_and_schedule_calls(self, file: bytes) -> str:
        """
        Create contacts and schedule calls from a file

        Args:
            file: File containing contacts and scheduling information

        Returns:
            Task group SID or status message
        """
        files = {"file": file}
        response = requests.post(
            f"{self.base_url}FtpReceptionServlet",
            files=files,
            headers={"Authorization": self.access_token},
        )
        return response.text

    def get_inbound_recordings(
        self,
        group_sid: Union[str, List[str]],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        recording_type: Optional[str] = None,
    ) -> bytes:
        """Get inbound recordings"""
        params = {
            "groupSid": (
                ",".join(group_sid) if isinstance(group_sid, list) else group_sid
            )
        }
        if start_date:
            params["startDate"] = start_date.strftime("%Y/%m/%d %H:%M")
        if end_date:
            params["endDate"] = end_date.strftime("%Y/%m/%d %H:%M")
        if recording_type:
            params["recordingType"] = recording_type

        response = requests.get(
            f"{self.base_url}RemoteInboundRecordingsList",
            params=params,
            headers={"Authorization": self.access_token},
        )
        return response.content

    def get_manual_dial_report(
        self,
        group_sid: Union[str, List[str]],
        template_number: Optional[int] = None,
        order_by: Optional[str] = None,
        custom_filter_name: Optional[str] = None,
    ) -> str:
        """Get manual dial call report"""
        params = {
            "groupSid": (
                ",".join(group_sid) if isinstance(group_sid, list) else group_sid
            )
        }
        if template_number:
            params["templateNumber"] = template_number
        if order_by:
            params["orderBy"] = order_by
        if custom_filter_name:
            params["customFilterName"] = custom_filter_name

        response = requests.get(
            f"{self.base_url}FtpManualDialReportServlet",
            params=params,
            headers={"Authorization": self.access_token},
        )
        return response.text

    def get_inbound_as_of_report(
        self,
        group_sid: str,
        start_id: Optional[str] = None,
        template_number: Optional[int] = None,
        custom_filter_name: Optional[str] = None,
    ) -> str:
        """Get inbound reports as they complete"""
        params = {"groupSid": group_sid}
        if start_id:
            params["startId"] = start_id
        if template_number:
            params["templateNumber"] = template_number
        if custom_filter_name:
            params["customFilterName"] = custom_filter_name

        response = requests.get(
            f"{self.base_url}FtpInboundReportAsOfServlet",
            params=params,
            headers={"Authorization": self.access_token},
        )
        return response.text

    def get_manual_dial_as_of_report(
        self,
        group_sid: str,
        start_id: Optional[str] = None,
        template_number: Optional[int] = None,
        custom_filter_name: Optional[str] = None,
    ) -> str:
        """Get manual dial reports as they complete"""
        params = {"groupSid": group_sid}
        if start_id:
            params["startId"] = start_id
        if template_number:
            params["templateNumber"] = template_number
        if custom_filter_name:
            params["customFilterName"] = custom_filter_name

        response = requests.get(
            f"{self.base_url}FtpManualDialReportAsOfServlet",
            params=params,
            headers={"Authorization": self.access_token},
        )
        return response.text

    def get_inbound_group_status(
        self,
        group_sid: Optional[Union[str, List[str]]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        extended: bool = False,
    ) -> str:
        """Get inbound group status"""
        params = {}
        if group_sid:
            params["groupSid"] = (
                ",".join(group_sid) if isinstance(group_sid, list) else group_sid
            )
        if start_date:
            params["startDate"] = start_date.strftime("%Y/%m/%d %H:%M")
        if end_date:
            params["endDate"] = end_date.strftime("%Y/%m/%d %H:%M")
        if extended:
            params["extended"] = str(extended).lower()

        response = requests.get(
            f"{self.base_url}RemoteInboundGroupStatusList",
            params=params,
            headers={"Authorization": self.access_token},
        )
        return response.text

    def get_manual_group_status(
        self,
        group_sid: Optional[Union[str, List[str]]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        extended: bool = False,
    ) -> str:
        """Get manual dial group status"""
        params = {}
        if group_sid:
            params["groupSid"] = (
                ",".join(group_sid) if isinstance(group_sid, list) else group_sid
            )
        if start_date:
            params["startDate"] = start_date.strftime("%Y/%m/%d %H:%M")
        if end_date:
            params["endDate"] = end_date.strftime("%Y/%m/%d %H:%M")
        if extended:
            params["extended"] = str(extended).lower()

        response = requests.get(
            f"{self.base_url}RemoteManualDialGroupStatusList",
            params=params,
            headers={"Authorization": self.access_token},
        )
        return response.text

    def update_broadcast_lines(
        self, task_sid: Union[str, List[str]], outbound: Union[int, str] = "same"
    ) -> str:
        """Update number of broadcast lines"""
        params = {
            "taskSid": ",".join(task_sid) if isinstance(task_sid, list) else task_sid,
            "outbound": outbound,
        }

        response = requests.post(
            f"{self.base_url}RemoteBroadcastLineControl",
            params=params,
            headers={"Authorization": self.access_token},
        )
        return response.text

    def delete_inbound_dncl_numbers(
        self, country: str, numbers: Union[str, List[str]]
    ) -> str:
        """Delete numbers from inbound DNCL"""
        params = {
            "country": country,
            "dncl_numbers": ",".join(numbers) if isinstance(numbers, list) else numbers,
        }

        response = requests.post(
            f"{self.base_url}RemoteInboundDNCLPurgeNumbers",
            params=params,
            headers={"Authorization": self.access_token},
        )
        return response.text

    def update_sms_groups(
        self,
        sms_group_sid: Union[str, List[str]],
        function: str,
        new_pace: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Control SMS campaigns"""
        params = {
            "smsGroupSid": (
                ",".join(sms_group_sid)
                if isinstance(sms_group_sid, list)
                else sms_group_sid
            ),
            "function": function,
        }
        if new_pace and function == "changePace":
            params["newPace"] = new_pace

        response = requests.post(
            f"{self.base_url}SmsGroupControl",
            params=params,
            headers={"Authorization": self.access_token},
        )
        return response.json()

    def create_sms_broadcast_with_file(self, file: bytes) -> str:
        """Create SMS broadcast from file"""
        files = {"file": file}

        response = requests.post(
            f"{self.base_url}SmsScheduleWithFile",
            files=files,
            headers={"Authorization": self.access_token},
        )
        return response.text

    def get_email_report(
        self,
        report_type: str,
        from_date: datetime,
        to_date: datetime,
        group_sid: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get email campaign report"""
        params = {
            "reportType": report_type,
            "fromDay": from_date.day,
            "fromMonth": from_date.month,
            "fromYear": from_date.year,
            "toDay": to_date.day,
            "toMonth": to_date.month,
            "toYear": to_date.year,
        }
        if group_sid:
            params["groupSid"] = group_sid

        response = requests.get(
            f"{self.base_url}EmailReport",
            params=params,
            headers={"Authorization": self.access_token},
        )
        return response.json()

    def create_email_broadcast_with_file(self, file: bytes) -> str:
        """Create email broadcast from file"""
        files = {"file": file}

        response = requests.post(
            f"{self.base_url}EmailScheduleWithFile",
            files=files,
            headers={"Authorization": self.access_token},
        )
        return response.text

    def add_lead_drip_drop_to_running_campaign(self, file: bytes) -> str:
        """Add contacts to running lead drip campaign"""
        files = {"file": file}

        response = requests.post(
            f"{self.base_url}SimpleLeadDripDrop",
            files=files,
            headers={"Authorization": self.access_token},
        )
        return response.text

    def update_agent_recording(
        self, agent_sid: str, client_sid: str, function: str
    ) -> str:
        """
        Control agent recording

        Args:
            agent_sid: Agent to control
            client_sid: Organization client ID
            function: Control action (get/pause/resume)

        Returns:
            Status message
        """
        params = {"agentSid": agent_sid, "clientSid": client_sid, "function": function}

        response = requests.post(
            f"{self.base_url}AgentRecordingCtrl",
            params=params,
            headers={"Authorization": self.access_token},
        )
        return response.text

    def get_outbound_recordings(
        self,
        task_sid: Union[str, List[str]],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        recording_type: Optional[str] = None,
    ) -> bytes:
        """
        Get outbound recordings

        Args:
            task_sid: Task SID(s) to get recordings for
            start_date: Optional start of date range
            end_date: Optional end of date range
            recording_type: Optional type filter (voicemail/linkback)

        Returns:
            Zip file containing recordings
        """
        params = {
            "taskSid": ",".join(task_sid) if isinstance(task_sid, list) else task_sid
        }

        if start_date:
            params["startDate"] = start_date.strftime("%Y/%m/%d %H:%M")
        if end_date:
            params["endDate"] = end_date.strftime("%Y/%m/%d %H:%M")
        if recording_type:
            params["recordingType"] = recording_type

        response = requests.get(
            f"{self.base_url}RemoteBroadcastRecordingsList",
            params=params,
            headers={"Authorization": self.access_token},
        )
        return response.content

    def delete_expired_outbound_dncl(self) -> str:
        """
        Delete expired numbers from outbound DNCL

        Returns:
            Status message
        """
        response = requests.post(
            f"{self.base_url}RemoteDNCLPurgeExpired",
            headers={"Authorization": self.access_token},
        )
        return response.text

    def delete_outbound_dncl_numbers(
        self, country: str, numbers: Union[str, List[str]]
    ) -> str:
        """
        Delete specific numbers from outbound DNCL

        Args:
            country: Country for numbers
            numbers: Phone number(s) to delete

        Returns:
            Status of deletion for each number
        """
        params = {
            "country": country,
            "dncl_numbers": ",".join(numbers) if isinstance(numbers, list) else numbers,
        }

        response = requests.post(
            f"{self.base_url}RemoteDNCLPurgeNumbers",
            params=params,
            headers={"Authorization": self.access_token},
        )
        return response.text

    def get_from_emails(self) -> Dict[str, Any]:
        """
        Get list of available from email addresses

        Returns:
            Available email addresses
        """
        response = requests.get(
            f"{self.base_url}EmailFromAddressList",
            headers={"Authorization": self.access_token},
        )
        return response.json()

    def get_scheduled_callback_report(
        self,
        start_date: datetime,
        end_date: Optional[datetime] = None,
        template_number: Optional[int] = None,
    ) -> str:
        """
        Get scheduled callbacks report

        Args:
            start_date: Start of date range
            end_date: Optional end of range
            template_number: Optional report template

        Returns:
            Report data
        """
        params = {"startDate": start_date.strftime("%Y/%m/%d %H:%M")}

        if end_date:
            params["endDate"] = end_date.strftime("%Y/%m/%d %H:%M")
        if template_number:
            params["templateNumber"] = template_number

        response = requests.get(
            f"{self.base_url}FtpScheduledCallbackReportServlet",
            params=params,
            headers={"Authorization": self.access_token},
        )
        return response.text

    def get_inbound_dncl(self, countries: Optional[List[str]] = None) -> str:
        """
        Get inbound Do Not Call List

        Args:
            countries: Optional country filters

        Returns:
            DNCL entries
        """
        params = {}
        if countries:
            params["country"] = ",".join(countries)

        response = requests.get(
            f"{self.base_url}RemoteInboundDNCLExport",
            params=params,
            headers={"Authorization": self.access_token},
        )
        return response.text

    def delete_inbound_dncl(self) -> str:
        """
        Delete entire inbound DNCL

        Returns:
            Status message
        """
        response = requests.post(
            f"{self.base_url}RemoteInboundDNCLPurge",
            headers={"Authorization": self.access_token},
        )
        return response.text

    def delete_expired_inbound_dncl(self) -> str:
        """
        Delete expired inbound DNCL numbers

        Returns:
            Status message
        """
        response = requests.post(
            f"{self.base_url}RemoteInboundDNCLPurgeExpired",
            headers={"Authorization": self.access_token},
        )
        return response.text

    def add_to_inbound_dncl(
        self,
        numbers: Union[str, List[str]],
        country_name: Optional[str] = None,
        expiration: Optional[datetime] = None,
        replace: bool = False,
        restrictive: bool = False,
        file: Optional[bytes] = None,
    ) -> str:
        """
        Add numbers to inbound DNCL

        Args:
            numbers: Number(s) to add
            country_name: Optional country
            expiration: Optional expiry date
            replace: Whether to purge existing
            restrictive: Use most restrictive expiry
            file: Optional file with numbers

        Returns:
            Status message
        """
        params = {"dncl": ",".join(numbers) if isinstance(numbers, list) else numbers}

        if country_name:
            params["country_name"] = country_name
        if expiration:
            params["exp_date"] = expiration.strftime("%Y/%m/%d %H:%M")
        if replace:
            params["replace"] = "true"
        if restrictive:
            params["restrictive"] = "true"

        files = {"file": file} if file else None

        response = requests.post(
            f"{self.base_url}RemoteInboundDNCLAdd",
            params=params,
            files=files,
            headers={"Authorization": self.access_token},
        )
        return response.text

    def get_agent_state_transitions(
        self, date: datetime, start_id: Optional[int] = None
    ) -> str:
        """
        Get agent state change details

        Args:
            date: Date to get transitions for
            start_id: Optional starting ID

        Returns:
            State transition records
        """
        params = {"day": date.strftime("%Y%m%d")}

        if start_id:
            params["startId"] = start_id

        response = requests.get(
            f"{self.base_url}RemoteAgentStateTransitionsExport",
            params=params,
            headers={"Authorization": self.access_token},
        )
        return response.text

    def get_available_agents_summary(self) -> Dict[str, Any]:
        """
        Get summary of current agent statuses

        Returns:
            Count of agents in each state
        """
        response = requests.get(
            f"{self.base_url}AgentSummary", headers={"Authorization": self.access_token}
        )
        return response.json()

    def create_scheduled_callbacks(self, file: bytes) -> str:
        """
        Create multiple scheduled callbacks

        Args:
            file: CSV with callback details

        Returns:
            Status message
        """
        files = {"file": file}

        response = requests.post(
            f"{self.base_url}ScheduleCallbacks",
            files=files,
            headers={"Authorization": self.access_token},
        )
        return response.text

    def get_broadcast_template_fields(self, template_number: int) -> str:
        """
        Get required TTS fields for broadcast template

        Args:
            template_number: Template to check

        Returns:
            Required field information
        """
        params = {"number": template_number}

        response = requests.get(
            f"{self.base_url}RemoteBroadcastTemplateRequiredTtsFieldList",
            params=params,
            headers={"Authorization": self.access_token},
        )
        return response.text

    def get_import_templates(self, extended: bool = False) -> str:
        """
        Get import templates

        Args:
            extended: Include additional template details

        Returns:
            Template information
        """
        params = {"extend": str(extended).lower()} if extended else {}

        response = requests.get(
            f"{self.base_url}RemoteImportTemplateList",
            params=params,
            headers={"Authorization": self.access_token},
        )
        return response.text

    def get_report_templates(self) -> str:
        """
        Get report templates

        Returns:
            Template information
        """
        response = requests.get(
            f"{self.base_url}RemoteReportTemplateList",
            headers={"Authorization": self.access_token},
        )
        return response.text

    def create_lead_drip_campaign(self, file: bytes) -> str:
        """
        Create lead drip campaign from file

        Args:
            file: File containing campaign config and optional contacts

        Returns:
            Task group SID or status
        """
        files = {"file": file}

        response = requests.post(
            f"{self.base_url}NewLeadDripCampaign",
            files=files,
            headers={"Authorization": self.access_token},
        )
        return response.text

    def add_lead_drip_drop(self, task_sid: str, file: bytes) -> str:
        """
        Add contacts to specific lead drip campaign

        Args:
            task_sid: Campaign to add to
            file: File containing contacts

        Returns:
            Status message
        """
        files = {"file": file}

        response = requests.post(
            f"{self.base_url}LeadDripDrop",
            files=files,
            headers={"Authorization": self.access_token},
        )
        return response.text

    def get_sms_source_numbers(self) -> Dict[str, Any]:
        """
        Get available SMS source numbers

        Returns:
            Available phone numbers
        """
        response = requests.get(
            f"{self.base_url}SmsSourceNumList",
            headers={"Authorization": self.access_token},
        )
        return response.json()

    def get_users(self, include_all: bool = False) -> Dict[str, Any]:
        """
        Get user list

        Args:
            include_all: Include non-agent users

        Returns:
            User details
        """
        params = {
            "function": "list",
            "includeUsers": "allUsers" if include_all else None,
        }

        response = requests.get(
            f"{self.base_url}AgentAcctMgmt",
            params=params,
            headers={"Authorization": self.access_token},
        )
        return response.json()

    def update_email_groups(
        self,
        email_group_sid: Union[str, List[str]],
        function: str,
        new_pace: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Control email campaigns

        Args:
            email_group_sid: Group SID(s) to control
            function: Control action (pause/unpause/cancel/status/changePace)
            new_pace: Required for changePace action

        Returns:
            Campaign status details
        """
        params = {
            "emailGroupSid": (
                ",".join(email_group_sid)
                if isinstance(email_group_sid, list)
                else email_group_sid
            ),
            "function": function,
        }

        if new_pace and function == "changePace":
            params["newPace"] = new_pace

        response = requests.post(
            f"{self.base_url}EmailGroupControl",
            params=params,
            headers={"Authorization": self.access_token},
        )
        return response.json()

    def get_outbound_dncl(self, countries: Optional[List[str]] = None) -> str:
        """
        Get outbound Do Not Call List

        Args:
            countries: Optional list of countries to filter by

        Returns:
            DNCL entries
        """
        params = {}
        if countries:
            params["country"] = ",".join(countries)

        response = requests.get(
            f"{self.base_url}RemoteDNCLExport",
            params=params,
            headers={"Authorization": self.access_token},
        )
        return response.text

    def delete_outbound_dncl(self) -> str:
        """
        Delete entire outbound Do Not Call List

        Returns:
            Status message
        """
        response = requests.post(
            f"{self.base_url}RemoteDNCLPurge",
            headers={"Authorization": self.access_token},
        )
        return response.text

    def get_outbound_as_of_report(
        self,
        task_sid: str,
        start_id: Optional[str] = None,
        template_number: Optional[int] = None,
        custom_filter_name: Optional[str] = None,
    ) -> str:
        """
        Get outbound reports as completed

        Args:
            task_sid: Campaign to get report for
            start_id: Optional starting call/record ID
            template_number: Optional report template
            custom_filter_name: Optional report filter

        Returns:
            Report data
        """
        params = {"taskSid": task_sid}

        if start_id:
            params["startId"] = start_id
        if template_number:
            params["templateNumber"] = template_number
        if custom_filter_name:
            params["customFilterName"] = custom_filter_name

        response = requests.get(
            f"{self.base_url}FtpReportAsOfServlet",
            params=params,
            headers={"Authorization": self.access_token},
        )
        return response.text

    def get_manual_dial_recordings(
        self,
        group_sid: Union[str, List[str]],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        recording_type: Optional[str] = None,
    ) -> bytes:
        """
        Get manual dial recordings

        Args:
            group_sid: Group SID(s) to get recordings for
            start_date: Optional start of date range
            end_date: Optional end of date range
            recording_type: Optional type filter (voicemail/linkback)

        Returns:
            Zip file containing recordings
        """
        params = {
            "groupSid": (
                ",".join(group_sid) if isinstance(group_sid, list) else group_sid
            )
        }

        if start_date:
            params["startDate"] = start_date.strftime("%Y/%m/%d %H:%M")
        if end_date:
            params["endDate"] = end_date.strftime("%Y/%m/%d %H:%M")
        if recording_type:
            params["recordingType"] = recording_type

        response = requests.get(
            f"{self.base_url}RemoteManualDialRecordingsList",
            params=params,
            headers={"Authorization": self.access_token},
        )
        return response.content

    def get_task_group_status(
        self,
        task_sid: Optional[Union[str, List[str]]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        extended: bool = False,
    ) -> str:
        """
        Get task group(s) status

        Args:
            task_sid: Optional task SID(s)
            start_date: Optional start of date range
            end_date: Optional end of date range
            extended: Include additional details

        Returns:
            Task group status information
        """
        params = {}
        if task_sid:
            params["taskSid"] = (
                ",".join(task_sid) if isinstance(task_sid, list) else task_sid
            )
        if start_date:
            params["startDate"] = start_date.strftime("%Y/%m/%d %H:%M")
        if end_date:
            params["endDate"] = end_date.strftime("%Y/%m/%d %H:%M")
        if extended:
            params["extended"] = str(extended).lower()

        response = requests.get(
            f"{self.base_url}RemoteBroadcastStatusList",
            params=params,
            headers={"Authorization": self.access_token},
        )
        return response.text

    def get_phone_number_activity(
        self,
        dialed_number: Optional[str] = None,
        days_of_history: int = 60,
        call_type: Union[str, List[str]] = "manual",
        caller_id: Optional[str] = None,
        call_sid: Optional[str] = None,
    ) -> str:
        """
        Get phone number activity history

        Args:
            dialed_number: Number to look up
            days_of_history: How far back to search
            call_type: Type(s) of calls to include
            caller_id: Optional caller ID filter
            call_sid: Optional specific call to look up

        Returns:
            Call activity records
        """
        params = {
            "days_of_history": days_of_history,
            "call_type": (
                ",".join(call_type) if isinstance(call_type, list) else call_type
            ),
        }

        if dialed_number:
            params["dialed_number"] = dialed_number
        if caller_id:
            params["caller_id"] = caller_id
        if call_sid:
            params["call_sid"] = call_sid

        response = requests.get(
            f"{self.base_url}RemoteNumberActivityList",
            params=params,
            headers={"Authorization": self.access_token},
        )
        return response.text

    def create_users(
        self, users: List[Dict[str, Any]], use_file: bool = False
    ) -> Dict[str, Any]:
        """
        Create new users

        Args:
            users: List of user details dictionaries
            use_file: Whether to send as file upload

        Returns:
            Creation status for each user
        """
        params = {"function": "addOrUpdate"}

        if use_file:
            # Convert users to CSV format
            file_content = ""
            for user in users:
                file_content += (
                    f"{user.get('first_name','')},{user.get('last_name','')}"
                )
                file_content += f",{user.get('username','')},{user.get('password','')}"
                file_content += f",,{user.get('hunt_group_sid','')}"
                file_content += f",{user.get('partner_agent_id','')},,"
                file_content += f"{user.get('agent','Agent')},{user.get('operator','')}"
                file_content += f",{user.get('backoffice','')}\n"

            files = {"agentAccts": ("users.csv", file_content)}
            response = requests.post(
                f"{self.base_url}AgentAcctMgmt",
                params=params,
                files=files,
                headers={"Authorization": self.access_token},
            )
        else:
            # Convert to parameter string
            user_str = "|".join(
                [
                    f"{u['first_name']},{u['last_name']},{u['username']},{u['password']}"
                    f",,{u.get('hunt_group_sid','')},{u.get('partner_agent_id','')},,"
                    f"{u.get('agent','Agent')},{u.get('operator','')},{u.get('backoffice','')}"
                    for u in users
                ]
            )
            params["agentAccts"] = user_str

            response = requests.post(
                f"{self.base_url}AgentAcctMgmt",
                params=params,
                headers={"Authorization": self.access_token},
            )

        return response.json()

    def get_sms_templates(self) -> Dict[str, Any]:
        """
        Get SMS templates

        Returns:
            Template details including IDs and content
        """
        response = requests.get(
            f"{self.base_url}SmsTemplateList",
            headers={"Authorization": self.access_token},
        )
        return response.json()

    def get_email_templates(self) -> Dict[str, Any]:
        """
        Get email templates

        Returns:
            Template details including IDs and content
        """
        response = requests.get(
            f"{self.base_url}EmailTemplateList",
            headers={"Authorization": self.access_token},
        )
        return response.json()

    def update_inbound_groups(
        self, group_sid: Union[str, List[str]], action: str
    ) -> str:
        """
        Control inbound groups

        Args:
            group_sid: Group SID(s) to control
            action: Control action (pause/play/stop)

        Returns:
            Status message
        """
        params = {
            "groupSid": (
                ",".join(group_sid) if isinstance(group_sid, list) else group_sid
            ),
            "action": action,
        }

        response = requests.post(
            f"{self.base_url}RemoteInboundGroupControl",
            params=params,
            headers={"Authorization": self.access_token},
        )
        return response.text

    def get_schedule_rules(self, extended: bool = False) -> str:
        """
        Get schedule rules

        Args:
            extended: Include additional rule details

        Returns:
            Schedule rule information
        """
        params = {"extended": str(extended).lower()} if extended else {}

        response = requests.get(
            f"{self.base_url}RemoteScheduleRuleList",
            params=params,
            headers={"Authorization": self.access_token},
        )
        return response.text

    def create_scheduled_callback(
        self,
        callback_name: str,
        phone_number: str,
        caller_id: str,
        target_agent_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        time_zone: Optional[str] = None,
        skills: Optional[List[str]] = None,
        notes: Optional[str] = None,
        country_name: Optional[str] = None,
    ) -> str:
        """
        Create a scheduled callback for an agent

        Args:
            callback_name: Name assigned to callback
            phone_number: Number to call back
            caller_id: Number calling from
            target_agent_id: Agent SID for callback
            start_time: When callback becomes available
            end_time: When callback expires
            time_zone: Timezone for times
            skills: Required agent skills
            notes: Additional notes
            country_name: Country for number

        Returns:
            Status message
        """
        params = {
            "callbackName": callback_name,
            "phoneNumber": phone_number,
            "callerId": caller_id,
            "targetAgentId": target_agent_id,
        }

        if start_time:
            params["startTime"] = start_time.strftime("%Y/%m/%d %H:%M")
        if end_time:
            params["endTime"] = end_time.strftime("%Y/%m/%d %H:%M")
        if time_zone:
            params["timeZone"] = time_zone
        if skills:
            params["skills"] = ",".join(skills)
        if notes:
            params["notes"] = notes
        if country_name:
            params["countryName"] = country_name

        response = requests.post(
            f"{self.base_url}ScheduleACallback",
            params=params,
            headers={"Authorization": self.access_token},
        )
        return response.text

    def get_outbound_report(
        self,
        task_sid: Union[str, List[str]],
        template_number: Optional[int] = None,
        filter_values: Optional[List[str]] = None,
        filter_type: Optional[str] = None,
        order_by: Optional[str] = None,
        custom_filter_name: Optional[str] = None,
    ) -> str:
        """
        Get report for outbound calls

        Args:
            task_sid: Task SID(s) for report
            template_number: Report template number
            filter_values: Result codes to filter
            filter_type: How to apply filter (include/exclude)
            order_by: Sort order for results
            custom_filter_name: Name of report filter

        Returns:
            Report data
        """
        params = {
            "taskSid": ",".join(task_sid) if isinstance(task_sid, list) else task_sid
        }

        if template_number:
            params["templateNumber"] = template_number
        if filter_values:
            params["filterValues"] = ",".join(filter_values)
        if filter_type:
            params["filter"] = filter_type
        if order_by:
            params["orderBy"] = order_by
        if custom_filter_name:
            params["customFilterName"] = custom_filter_name

        response = requests.get(
            f"{self.base_url}FtpReportServlet",
            params=params,
            headers={"Authorization": self.access_token},
        )
        return response.text

    def update_broadcasts(self, task_sid: Union[str, List[str]], action: str) -> str:
        """
        Control outbound broadcasts

        Args:
            task_sid: Task SID(s) to control
            action: Control action (pause/play/stop)

        Returns:
            Status message
        """
        params = {
            "taskSid": ",".join(task_sid) if isinstance(task_sid, list) else task_sid,
            "action": action,
        }

        response = requests.post(
            f"{self.base_url}RemoteBroadcastControl",
            params=params,
            headers={"Authorization": self.access_token},
        )
        return response.text

    def get_agent_status(self, agent_sid: Optional[str] = None) -> Dict[str, Any]:
        """
        Get status of logged in agents

        Args:
            agent_sid: Optional specific agent to check

        Returns:
            Agent status details
        """
        params = {}
        if agent_sid:
            params["agentSid"] = agent_sid

        response = requests.get(
            f"{self.base_url}AgentStatus",
            params=params,
            headers={"Authorization": self.access_token},
        )
        return response.json()

    def create_sms_broadcast(
        self,
        template_sid: str,
        contact_group_sid: str,
        src_num: str,
        phone_num_col: str,
        pace: Optional[int] = None,
        start_time: Optional[datetime] = None,
        stop_time: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Create SMS broadcast campaign

        Args:
            template_sid: SMS template ID
            contact_group_sid: Contact group to message
            src_num: Source phone number
            phone_num_col: Column with phone numbers
            pace: Messages per minute
            start_time: When to start sending
            stop_time: When to stop sending

        Returns:
            Campaign details including group SID
        """
        params = {
            "templateSid": template_sid,
            "contactGroupSid": contact_group_sid,
            "srcNum": src_num,
            "phoneNumCol": phone_num_col,
        }

        if pace:
            params["pace"] = pace

        if start_time:
            params.update(
                {
                    "startYear": start_time.year,
                    "startMonth": start_time.month,
                    "startDay": start_time.day,
                    "startHour": start_time.hour,
                    "startMinute": start_time.minute,
                }
            )

        if stop_time:
            params.update(
                {
                    "stopYear": stop_time.year,
                    "stopMonth": stop_time.month,
                    "stopDay": stop_time.day,
                    "stopHour": stop_time.hour,
                    "stopMinute": stop_time.minute,
                }
            )

        response = requests.post(
            f"{self.base_url}SmsSchedule",
            params=params,
            headers={"Authorization": self.access_token},
        )
        return response.json()

    def get_recording_file(
        self,
        hash_value: str,
        call_sid: str,
        call_log_sid: str,
        recording_type: str,
        category: Optional[str] = None,
        link_call_extension: Optional[str] = None,
    ) -> bytes:
        """
        Get recording file for a call

        Args:
            hash_value: Hash identifying recording
            call_sid: Call SID
            call_log_sid: Call log SID
            recording_type: Type (outbound/inbound/manual)
            category: Optional category (linkback/voicemail/etc)
            link_call_extension: Optional format (wav/mp3)

        Returns:
            Recording file bytes
        """
        params = {
            "hash": hash_value,
            "cs": call_sid,
            "cls": call_log_sid,
            "type": recording_type,
        }

        if category:
            params["category"] = category
        if link_call_extension:
            params["linkcallExtension"] = link_call_extension

        response = requests.get(
            f"{self.base_url}RetrieveRecordingFile",
            params=params,
            headers={"Authorization": self.access_token},
        )
        return response.content

    def update_agent_state(self, agent_sid: str, new_state: str) -> str:
        """
        Change agent state

        Args:
            agent_sid: Agent to update
            new_state: New state (logout/ready/paused/wrapup)

        Returns:
            Status message
        """
        params = {"agentSid": agent_sid, "newState": new_state}

        response = requests.post(
            f"{self.base_url}ChangeAgentState",
            params=params,
            headers={"Authorization": self.access_token},
        )
        return response.text

    def get_broadcast_templates(self) -> str:
        """
        Get list of broadcast templates

        Returns:
            CSV data with template info
        """
        response = requests.get(
            f"{self.base_url}RemoteBroadcastTemplateList",
            headers={"Authorization": self.access_token},
        )
        return response.text

    def add_to_outbound_dncl(
        self,
        numbers: Union[str, List[str]],
        country_name: Optional[str] = None,
        expiration: Optional[datetime] = None,
        replace: bool = False,
        restrictive: bool = False,
        file: Optional[bytes] = None,
    ) -> str:
        """
        Add numbers to outbound Do Not Call List

        Args:
            numbers: Phone number(s) to add
            country_name: Optional country
            expiration: Optional expiration date
            replace: Whether to purge existing list
            restrictive: Use most restrictive expiration
            file: Optional file with additional numbers

        Returns:
            Status message
        """
        params = {"dncl": ",".join(numbers) if isinstance(numbers, list) else numbers}

        if country_name:
            params["country_name"] = country_name
        if expiration:
            params["exp_date"] = expiration.strftime("%Y/%m/%d %H:%M")
        if replace:
            params["replace"] = "true"
        if restrictive:
            params["restrictive"] = "true"

        files = {"file": file} if file else None

        response = requests.post(
            f"{self.base_url}RemoteDNCLAdd",
            params=params,
            files=files,
            headers={"Authorization": self.access_token},
        )
        return response.text

    def create_email_broadcast(
        self,
        template_sid: str,
        contact_group_sid: str,
        from_address: str,
        email_col: str,
        schedule_duplicates: bool = False,
        pace: Optional[int] = None,
        start_time: Optional[datetime] = None,
        stop_time: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Create email broadcast campaign

        Args:
            template_sid: Email template ID
            contact_group_sid: Contact group to email
            from_address: Sender email address
            email_col: Column with email addresses
            schedule_duplicates: Allow duplicate contacts
            pace: Emails per minute
            start_time: When to start sending
            stop_time: When to stop sending

        Returns:
            Campaign details including group SID
        """
        params = {
            "templateSid": template_sid,
            "contactGroupSid": contact_group_sid,
            "fromAddress": from_address,
            "emailCol": email_col,
            "scheduleDuplicates": str(schedule_duplicates).lower(),
        }

        if pace:
            params["pace"] = pace

        if start_time:
            params.update(
                {
                    "startYear": start_time.year,
                    "startMonth": start_time.month,
                    "startDay": start_time.day,
                    "startHour": start_time.hour,
                    "startMinute": start_time.minute,
                }
            )

        if stop_time:
            params.update(
                {
                    "stopYear": stop_time.year,
                    "stopMonth": stop_time.month,
                    "stopDay": stop_time.day,
                    "stopHour": stop_time.hour,
                    "stopMinute": stop_time.minute,
                }
            )

        response = requests.post(
            f"{self.base_url}EmailSchedule",
            params=params,
            headers={"Authorization": self.access_token},
        )
        return response.json()

    def get_contact_groups(self) -> Dict[str, Any]:
        """
        Get list of contact groups

        Returns:
            Contact group details
        """
        response = requests.get(
            f"{self.base_url}ContactGroupList",
            headers={"Authorization": self.access_token},
        )
        return response.json()

    def get_inbound_report(
        self,
        group_sid: Union[str, List[str]],
        template_number: Optional[int] = None,
        order_by: Optional[str] = None,
        custom_filter_name: Optional[str] = None,
    ) -> str:
        """
        Get report for inbound calls

        Args:
            group_sid: Group SID(s) for report
            template_number: Report template number
            order_by: Sort order for results
            custom_filter_name: Name of report filter

        Returns:
            Report data
        """
        params = {
            "groupSid": (
                ",".join(group_sid) if isinstance(group_sid, list) else group_sid
            )
        }

        if template_number:
            params["templateNumber"] = template_number
        if order_by:
            params["orderBy"] = order_by
        if custom_filter_name:
            params["customFilterName"] = custom_filter_name

        response = requests.get(
            f"{self.base_url}FtpInboundReportServlet",
            params=params,
            headers={"Authorization": self.access_token},
        )
        return response.text

    def get_agent_skills(self, extended: bool = False) -> str:
        """
        Get list of agent skills

        Args:
            extended: Include additional skill details

        Returns:
            Agent skill information
        """
        params = {"extended": str(extended).lower()} if extended else {}

        response = requests.get(
            f"{self.base_url}RemoteAgentSkillsList",
            params=params,
            headers={"Authorization": self.access_token},
        )
        return response.text
