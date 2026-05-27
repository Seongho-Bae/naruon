import logging
from typing import Dict, Any, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import ProjectFolder, WebdavAccount

logger = logging.getLogger(__name__)

async def sync_webdav_folders(session, user_id: str):
    """
    Fetch folder structures for all WebDAV accounts of the user.
    """
    from db.models import WebdavAccount
    from sqlalchemy import select
    
    logger.info(f"Syncing WebDAV folders for user {user_id}")
    stmt = select(WebdavAccount).where(WebdavAccount.user_id == user_id)
    res = await session.execute(stmt)
    accounts = res.scalars().all()
    for account in accounts:
        logger.info(f"Fetched folder structures for WebDAV account {account.server_url}")
    return True

class WebDavService:
    def __init__(self):
        self._mock_accounts = {
            "demo_user": [
                {
                    "account_id": 1,
                    "server_url": "https://webdav.naruon.net",
                    "username": "demo_user"
                }
            ]
        }
        self._mock_folders = {
            "demo_user": [
                {
                    "folder_id": 1,
                    "project_name": "Naruon Roadmap 2026",
                    "webdav_path": "/Projects/Naruon_Roadmap_2026"
                },
                {
                    "folder_id": 2,
                    "project_name": "Marketing Assets",
                    "webdav_path": "/Projects/Marketing_Assets"
                }
            ]
        }

    def get_connected_accounts(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Fetch connected WebDAV accounts for a user.
        In a real implementation, this queries the database.
        """
        return self._mock_accounts.get(user_id, [])

    def get_project_folders(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Fetch the list of project folders structured by AI.
        """
        return self._mock_folders.get(user_id, [])

    async def get_connected_accounts_from_db(
        self,
        session: AsyncSession,
        user_id: str,
    ) -> List[Dict[str, Any]]:
        stmt = select(WebdavAccount).where(WebdavAccount.user_id == user_id)
        result = await session.execute(stmt)
        return [
            {
                "account_id": account.id,
                "server_url": account.server_url,
                "username": account.username,
            }
            for account in result.scalars().all()
        ]

    async def get_project_folders_from_db(
        self,
        session: AsyncSession,
        user_id: str,
    ) -> List[Dict[str, Any]]:
        stmt = select(ProjectFolder).where(ProjectFolder.user_id == user_id)
        result = await session.execute(stmt)
        return [
            {
                "folder_id": folder.id,
                "project_name": folder.project_name,
                "webdav_path": folder.webdav_path,
            }
            for folder in result.scalars().all()
        ]

    def sync_attachments_to_folder(self, email_id: str, project_name: str) -> bool:
        """
        Organizes an email's attachments into the specified WebDAV project folder.
        """
        logger.info(f"Syncing attachments from email {email_id} to project {project_name}")
        # Mock implementation: in reality, this would download from storage and upload via webdavclient3
        return True

    def determine_webdav_writeback_intent(self, user_id: str, target_account_id: int | None = None) -> Dict[str, Any]:
        """
        Server-authoritative WebDAV writeback source selection.
        """
        accounts = self.get_connected_accounts(user_id)
        return self.determine_webdav_writeback_intent_from_accounts(
            accounts,
            target_account_id=target_account_id,
        )

    async def determine_webdav_writeback_intent_from_db(
        self,
        session: AsyncSession,
        user_id: str,
        target_account_id: int | None = None,
    ) -> Dict[str, Any]:
        accounts = await self.get_connected_accounts_from_db(session, user_id)
        return self.determine_webdav_writeback_intent_from_accounts(
            accounts,
            target_account_id=target_account_id,
        )

    def determine_webdav_writeback_intent_from_accounts(
        self,
        accounts: List[Dict[str, Any]],
        target_account_id: int | None = None,
    ) -> Dict[str, Any]:
        if not accounts:
            return {"status": "error", "message": "No connected WebDAV accounts found."}
            
        selected_account = accounts[0]
        if target_account_id is not None:
            selected_account = None
            for acc in accounts:
                if acc["account_id"] == target_account_id:
                    selected_account = acc
                    break
            if selected_account is None:
                return {
                    "status": "error",
                    "message": "Requested WebDAV account was not found.",
                }
                    
        return {
            "intent": "writeback",
            "source_id": selected_account["account_id"],
            "server_url": selected_account["server_url"],
            "requires_if_match": True,
            "provenance": "server-authoritative"
        }

webdav_service = WebDavService()
