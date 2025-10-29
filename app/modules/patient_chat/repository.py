"""
Chat Repository - Database operations for messages and chat rooms
Uses existing database connection from app.core.database
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from pymongo import DESCENDING, ASCENDING
from pymongo.collection import Collection
import logging

from app.modules.patient_chat.models import Message, ChatRoom, MessageAttachment, MessageReaction

logger = logging.getLogger(__name__)


class ChatRepository:
    """Repository for chat-related database operations"""
    
    def __init__(self, db):
        """
        Initialize repository with database connection
        
        Args:
            db: Database instance from app.core.database
        """
        self.db = db
        self.messages_collection = None
        self.chat_rooms_collection = None
        self._init_collections()
    
    def _init_collections(self):
        """Initialize chat collections"""
        try:
            # Get or create collections using the Database class methods
            if self.db.client:
                self.messages_collection = self.db.get_collection('chat_messages')
                self.chat_rooms_collection = self.db.get_collection('chat_rooms')
                
                # Create indexes for better performance
                self._create_indexes()
                
                logger.info("Chat collections initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize chat collections: {str(e)}")
            raise
    
    def _create_indexes(self):
        """Create database indexes for chat collections"""
        try:
            # Message indexes
            self.messages_collection.create_index([("chat_room_id", ASCENDING)])
            self.messages_collection.create_index([("message_id", ASCENDING)], unique=True)
            self.messages_collection.create_index([("sender_id", ASCENDING)])
            self.messages_collection.create_index([("receiver_id", ASCENDING)])
            self.messages_collection.create_index([("created_at", DESCENDING)])
            self.messages_collection.create_index([
                ("chat_room_id", ASCENDING),
                ("created_at", DESCENDING)
            ])
            
            # Chat room indexes
            self.chat_rooms_collection.create_index([("room_id", ASCENDING)], unique=True)
            self.chat_rooms_collection.create_index([("doctor_id", ASCENDING)])
            self.chat_rooms_collection.create_index([("patient_id", ASCENDING)])
            self.chat_rooms_collection.create_index([
                ("doctor_id", ASCENDING),
                ("patient_id", ASCENDING)
            ], unique=True)
            
            logger.info("Chat indexes created successfully")
        except Exception as e:
            logger.warning(f"Some indexes may already exist: {str(e)}")
    
    # ==================== Chat Room Operations ====================
    
    def create_chat_room(self, doctor_id: str, patient_id: str) -> Optional[ChatRoom]:
        """
        Create a new chat room or return existing one
        
        Args:
            doctor_id: Doctor ID
            patient_id: Patient ID
        
        Returns:
            ChatRoom object or None
        """
        try:
            # Check if room already exists
            existing_room = self.get_chat_room_by_participants(doctor_id, patient_id)
            if existing_room:
                return existing_room
            
            # Create new room
            chat_room = ChatRoom(doctor_id=doctor_id, patient_id=patient_id)
            
            # Validate
            errors = chat_room.validate()
            if errors:
                logger.error(f"Chat room validation failed: {errors}")
                return None
            
            # Insert into database
            result = self.chat_rooms_collection.insert_one(chat_room.to_dict())
            
            if result.inserted_id:
                logger.info(f"Created chat room: {chat_room.room_id}")
                return chat_room
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to create chat room: {str(e)}")
            return None
    
    def get_chat_room(self, room_id: str) -> Optional[ChatRoom]:
        """
        Get a chat room by ID
        
        Args:
            room_id: Room ID
        
        Returns:
            ChatRoom object or None
        """
        try:
            room_data = self.chat_rooms_collection.find_one({"room_id": room_id})
            if room_data:
                return ChatRoom.from_dict(room_data)
            return None
        except Exception as e:
            logger.error(f"Failed to get chat room: {str(e)}")
            return None
    
    def get_chat_room_by_participants(self, doctor_id: str, patient_id: str) -> Optional[ChatRoom]:
        """
        Get a chat room by doctor and patient IDs
        
        Args:
            doctor_id: Doctor ID
            patient_id: Patient ID
        
        Returns:
            ChatRoom object or None
        """
        try:
            room_data = self.chat_rooms_collection.find_one({
                "doctor_id": doctor_id,
                "patient_id": patient_id
            })
            if room_data:
                return ChatRoom.from_dict(room_data)
            return None
        except Exception as e:
            logger.error(f"Failed to get chat room by participants: {str(e)}")
            return None
    
    def get_user_chat_rooms(self, user_id: str, user_type: str) -> List[Dict[str, Any]]:
        """
        Get all chat rooms for a user
        
        Args:
            user_id: User ID
            user_type: User type (patient or doctor)
        
        Returns:
            List of chat room dictionaries
        """
        try:
            query = {}
            if user_type == "patient":
                query["patient_id"] = user_id
            elif user_type == "doctor":
                query["doctor_id"] = user_id
            else:
                return []
            
            rooms = list(self.chat_rooms_collection.find(query).sort("updated_at", DESCENDING))
            # Convert ObjectId to string for JSON serialization
            for room in rooms:
                if '_id' in room:
                    room['_id'] = str(room['_id'])
            return rooms
            
        except Exception as e:
            logger.error(f"Failed to get user chat rooms: {str(e)}")
            return []
    
    def update_chat_room_last_message(self, room_id: str, message: str, 
                                     message_time: datetime) -> bool:
        """
        Update the last message in a chat room
        
        Args:
            room_id: Room ID
            message: Last message content
            message_time: Message timestamp
        
        Returns:
            bool: Success status
        """
        try:
            result = self.chat_rooms_collection.update_one(
                {"room_id": room_id},
                {
                    "$set": {
                        "last_message": message,
                        "last_message_time": message_time,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Failed to update chat room last message: {str(e)}")
            return False
    
    def increment_unread_count(self, room_id: str, user_type: str) -> bool:
        """
        Increment unread message count for a user in a room
        
        Args:
            room_id: Room ID
            user_type: User type (patient or doctor)
        
        Returns:
            bool: Success status
        """
        try:
            field = f"unread_count_{user_type}"
            result = self.chat_rooms_collection.update_one(
                {"room_id": room_id},
                {"$inc": {field: 1}}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Failed to increment unread count: {str(e)}")
            return False
    
    def reset_unread_count(self, room_id: str, user_type: str) -> bool:
        """
        Reset unread message count for a user in a room
        
        Args:
            room_id: Room ID
            user_type: User type (patient or doctor)
        
        Returns:
            bool: Success status
        """
        try:
            field = f"unread_count_{user_type}"
            result = self.chat_rooms_collection.update_one(
                {"room_id": room_id},
                {"$set": {field: 0}}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Failed to reset unread count: {str(e)}")
            return False
    
    # ==================== Message Operations ====================
    
    def create_message(self, message: Message) -> Optional[Message]:
        """
        Create a new message
        
        Args:
            message: Message object
        
        Returns:
            Message object or None
        """
        try:
            # Validate
            errors = message.validate()
            if errors:
                logger.error(f"Message validation failed: {errors}")
                return None
            
            # Insert into database
            result = self.messages_collection.insert_one(message.to_dict())
            
            if result.inserted_id:
                # Update chat room
                self.update_chat_room_last_message(
                    message.chat_room_id,
                    message.content[:100],  # Store first 100 chars
                    message.created_at
                )
                
                # Increment unread count for receiver
                self.increment_unread_count(message.chat_room_id, message.receiver_type)
                
                logger.info(f"Created message: {message.message_id}")
                return message
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to create message: {str(e)}")
            return None
    
    def get_message(self, message_id: str) -> Optional[Message]:
        """
        Get a message by ID
        
        Args:
            message_id: Message ID
        
        Returns:
            Message object or None
        """
        try:
            message_data = self.messages_collection.find_one({"message_id": message_id})
            if message_data:
                return Message.from_dict(message_data)
            return None
        except Exception as e:
            logger.error(f"Failed to get message: {str(e)}")
            return None
    
    def get_chat_messages(self, room_id: str, page: int = 1, 
                         limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get messages from a chat room with pagination
        
        Args:
            room_id: Room ID
            page: Page number (1-indexed)
            limit: Messages per page
        
        Returns:
            List of message dictionaries
        """
        try:
            skip = (page - 1) * limit
            
            messages = list(
                self.messages_collection.find({"chat_room_id": room_id})
                .sort("created_at", DESCENDING)
                .skip(skip)
                .limit(limit)
            )
            
            # Convert ObjectId to string
            for msg in messages:
                if '_id' in msg:
                    msg['_id'] = str(msg['_id'])
            
            # Reverse to get chronological order
            return list(reversed(messages))
            
        except Exception as e:
            logger.error(f"Failed to get chat messages: {str(e)}")
            return []
    
    def mark_message_as_read(self, message_id: str, reader_id: str) -> bool:
        """
        Mark a specific message as read
        
        Args:
            message_id: Message ID
            reader_id: ID of the user marking as read
        
        Returns:
            bool: Success status
        """
        try:
            result = self.messages_collection.update_one(
                {"message_id": message_id},
                {
                    "$addToSet": {"read_by": reader_id},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Failed to mark message as read: {str(e)}")
            return False
    
    def mark_room_messages_as_read(self, room_id: str, reader_id: str) -> bool:
        """
        Mark all messages in a room as read for a user
        
        Args:
            room_id: Room ID
            reader_id: ID of the user marking as read
        
        Returns:
            bool: Success status
        """
        try:
            result = self.messages_collection.update_many(
                {
                    "chat_room_id": room_id,
                    "receiver_id": reader_id
                },
                {
                    "$addToSet": {"read_by": reader_id},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Failed to mark room messages as read: {str(e)}")
            return False
    
    def get_unread_message_count(self, user_id: str, user_type: str) -> int:
        """
        Get total unread message count for a user
        
        Args:
            user_id: User ID
            user_type: User type
        
        Returns:
            int: Unread message count
        """
        try:
            count = self.messages_collection.count_documents({
                "receiver_id": user_id,
                "receiver_type": user_type,
                "is_read": False
            })
            return count
        except Exception as e:
            logger.error(f"Failed to get unread message count: {str(e)}")
            return 0
    
    def edit_message(self, message_id: str, new_content: str) -> bool:
        """
        Edit a message
        
        Args:
            message_id: Message ID
            new_content: New message content
        
        Returns:
            bool: Success status
        """
        try:
            result = self.messages_collection.update_one(
                {"message_id": message_id},
                {
                    "$set": {
                        "content": new_content,
                        "is_edited": True,
                        "edited_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Failed to edit message: {str(e)}")
            return False
    
    def delete_message(self, message_id: str) -> bool:
        """
        Soft delete a message
        
        Args:
            message_id: Message ID
        
        Returns:
            bool: Success status
        """
        try:
            result = self.messages_collection.update_one(
                {"message_id": message_id},
                {
                    "$set": {
                        "is_deleted": True,
                        "deleted_at": datetime.utcnow(),
                        "content": "[Message deleted]"
                    }
                }
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Failed to delete message: {str(e)}")
            return False
    
    def search_messages(self, user_id: str, user_type: str, 
                       search_query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search messages for a user
        
        Args:
            user_id: User ID
            user_type: User type
            search_query: Search query
            limit: Maximum results
        
        Returns:
            List of message dictionaries
        """
        try:
            # Build query based on user type
            base_query = {
                "$or": [
                    {"sender_id": user_id, "sender_type": user_type},
                    {"receiver_id": user_id, "receiver_type": user_type}
                ],
                "content": {"$regex": search_query, "$options": "i"}
            }
            
            messages = list(
                self.messages_collection.find(base_query)
                .sort("created_at", DESCENDING)
                .limit(limit)
            )
            
            # Convert ObjectId to string
            for msg in messages:
                if '_id' in msg:
                    msg['_id'] = str(msg['_id'])
            
            return messages
            
        except Exception as e:
            logger.error(f"Failed to search messages: {str(e)}")
            return []
    

# Global repository instance
chat_repository = None


def init_chat_repository(db):
    """
    Initialize the global chat repository
    
    Args:
        db: Database instance
    
    Returns:
        ChatRepository instance
    """
    global chat_repository
    chat_repository = ChatRepository(db)
    return chat_repository


def get_chat_repository():
    """
    Get the global chat repository instance
    
    Returns:
        ChatRepository instance
    
    Raises:
        RuntimeError: If repository hasn't been initialized
    """
    if chat_repository is None:
        raise RuntimeError(
            "Chat repository has not been initialized. "
            "Call init_chat_repository(db) first."
        )
    return chat_repository
