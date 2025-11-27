"""
Backend API Client
==================

Handles all communication with the FastAPI backend.
"""

import streamlit as st
import requests
from typing import Optional, Dict, Any, List


class BackendClient:
    """API client for backend communication"""

    def __init__(self, api_url: str):
        self.api_url = api_url

    def check_health(self) -> bool:
        """
        Check if backend is reachable and healthy

        Returns:
            bool: True if backend is online, False otherwise
        """
        try:
            response = requests.get(f"{self.api_url}/health", timeout=3)
            return response.ok
        except requests.exceptions.RequestException:
            return False

    def create_session(self) -> Optional[Dict[str, Any]]:
        """
        Create a new chat session

        Returns:
            Optional[Dict]: Session data or None on error
        """
        try:
            with st.spinner("Creating new chat session..."):
                response = requests.post(f"{self.api_url}/sessions/new", timeout=10)
                response.raise_for_status()
                return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"Failed to create session: {str(e)}")
            return None

    def list_sessions(self) -> List[Dict[str, Any]]:
        """
        Load list of all sessions

        Returns:
            List[Dict]: List of session dictionaries
        """
        try:
            response = requests.get(f"{self.api_url}/sessions", timeout=5)
            response.raise_for_status()
            data = response.json()
            return data.get("sessions", [])
        except requests.exceptions.RequestException as e:
            st.error(f"Failed to load sessions: {str(e)}")
            return []

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Load a specific session

        Args:
            session_id: The session ID to load

        Returns:
            Optional[Dict]: Session data or None on error
        """
        try:
            with st.spinner("Loading session..."):
                response = requests.get(f"{self.api_url}/sessions/{session_id}", timeout=5)
                response.raise_for_status()
                return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"Failed to load session: {str(e)}")
            return None

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session

        Args:
            session_id: The session ID to delete

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with st.spinner("Deleting session..."):
                response = requests.delete(f"{self.api_url}/sessions/{session_id}", timeout=5)
                response.raise_for_status()
                return True
        except requests.exceptions.RequestException as e:
            st.error(f"Failed to delete session: {str(e)}")
            return False

    def send_message(self, session_id: str, message: str) -> Optional[Dict[str, Any]]:
        """
        Send a message in a session and get response

        Args:
            session_id: The session ID
            message: The user's message

        Returns:
            Optional[Dict]: Response data or None on error
        """
        try:
            with st.spinner("Assistant is thinking..."):
                response = requests.post(
                    f"{self.api_url}/sessions/{session_id}/chat",
                    json={"message": message},
                    timeout=30
                )
                response.raise_for_status()
                return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"Failed to send message: {str(e)}")
            return None

    def get_preview(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get live TFVARS preview for session

        Args:
            session_id: The session ID

        Returns:
            Optional[Dict]: Preview data with preview content, completion %, etc.
        """
        try:
            response = requests.get(f"{self.api_url}/sessions/{session_id}/preview", timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException:
            return None
