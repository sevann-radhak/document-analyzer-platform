"""Unit tests for base repository."""
import pytest
from unittest.mock import Mock, MagicMock, patch
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.repositories.base_repository import BaseRepository
from app.models.file import File
from datetime import datetime, timezone


class TestBaseRepository:
    """Test cases for BaseRepository class."""
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = Mock(spec=Session)
        return db
    
    @pytest.fixture
    def base_repository(self, mock_db):
        """Create a BaseRepository instance for testing."""
        return BaseRepository(mock_db, File)
    
    @pytest.fixture
    def sample_file(self):
        """Create a sample File instance."""
        file = MagicMock(spec=File)
        file.id = 1
        file.filename = "test.csv"
        file.s3_key = "uploads/2024/12/test.csv"
        file.uploaded_by = 1
        file.created_at = datetime.now(timezone.utc)
        return file
    
    def test_init(self, mock_db):
        """Test that repository initializes correctly."""
        repo = BaseRepository(mock_db, File)
        assert repo.db == mock_db
        assert repo.model == File
    
    def test_get_by_id_success(self, base_repository, mock_db, sample_file):
        """Test get_by_id returns entity when found."""
        mock_query = Mock()
        mock_filter = Mock()
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = sample_file
        mock_db.query.return_value = mock_query
        
        result = base_repository.get_by_id(1)
        
        assert result == sample_file
        mock_db.query.assert_called_once_with(File)
        mock_query.filter.assert_called_once()
        mock_filter.first.assert_called_once()
    
    def test_get_by_id_not_found(self, base_repository, mock_db):
        """Test get_by_id returns None when not found."""
        mock_query = Mock()
        mock_filter = Mock()
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = None
        mock_db.query.return_value = mock_query
        
        result = base_repository.get_by_id(999)
        
        assert result is None
    
    def test_get_by_id_handles_sqlalchemy_error(self, base_repository, mock_db):
        """Test get_by_id handles SQLAlchemyError gracefully."""
        mock_db.query.side_effect = SQLAlchemyError("Database error")
        
        result = base_repository.get_by_id(1)
        
        assert result is None
    
    def test_list_all_success(self, base_repository, mock_db, sample_file):
        """Test list_all returns list of entities."""
        mock_query = Mock()
        mock_order_by = Mock()
        mock_offset = Mock()
        mock_limit = Mock()
        
        mock_query.order_by.return_value = mock_order_by
        mock_order_by.offset.return_value = mock_offset
        mock_offset.limit.return_value = mock_limit
        mock_limit.all.return_value = [sample_file]
        mock_db.query.return_value = mock_query
        
        result = base_repository.list_all(skip=0, limit=10)
        
        assert result == [sample_file]
        assert len(result) == 1
        mock_db.query.assert_called_once_with(File)
    
    def test_list_all_with_pagination(self, base_repository, mock_db):
        """Test list_all respects pagination parameters."""
        mock_query = Mock()
        mock_order_by = Mock()
        mock_offset = Mock()
        mock_limit = Mock()
        
        mock_query.order_by.return_value = mock_order_by
        mock_order_by.offset.return_value = mock_offset
        mock_offset.limit.return_value = mock_limit
        mock_limit.all.return_value = []
        mock_db.query.return_value = mock_query
        
        base_repository.list_all(skip=10, limit=20)
        
        mock_order_by.offset.assert_called_once_with(10)
        mock_offset.limit.assert_called_once_with(20)
    
    def test_list_all_handles_sqlalchemy_error(self, base_repository, mock_db):
        """Test list_all handles SQLAlchemyError gracefully."""
        mock_db.query.side_effect = SQLAlchemyError("Database error")
        
        result = base_repository.list_all()
        
        assert result == []
    
    def test_count_all_success(self, base_repository, mock_db):
        """Test count_all returns correct count."""
        mock_query = Mock()
        mock_query.count.return_value = 5
        mock_db.query.return_value = mock_query
        
        result = base_repository.count_all()
        
        assert result == 5
        mock_db.query.assert_called_once_with(File)
        mock_query.count.assert_called_once()
    
    def test_count_all_handles_sqlalchemy_error(self, base_repository, mock_db):
        """Test count_all handles SQLAlchemyError gracefully."""
        mock_db.query.side_effect = SQLAlchemyError("Database error")
        
        result = base_repository.count_all()
        
        assert result == 0
    
    def test_delete_success(self, base_repository, mock_db, sample_file):
        """Test delete removes entity successfully."""
        mock_query = Mock()
        mock_filter = Mock()
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = sample_file
        mock_db.query.return_value = mock_query
        
        result = base_repository.delete(1)
        
        assert result is True
        mock_db.delete.assert_called_once_with(sample_file)
        mock_db.commit.assert_called_once()
    
    def test_delete_not_found(self, base_repository, mock_db):
        """Test delete returns False when entity not found."""
        mock_query = Mock()
        mock_filter = Mock()
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = None
        mock_db.query.return_value = mock_query
        
        result = base_repository.delete(999)
        
        assert result is False
        mock_db.delete.assert_not_called()
    
    def test_delete_handles_sqlalchemy_error(self, base_repository, mock_db, sample_file):
        """Test delete handles SQLAlchemyError gracefully."""
        mock_query = Mock()
        mock_filter = Mock()
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = sample_file
        mock_db.query.return_value = mock_query
        mock_db.commit.side_effect = SQLAlchemyError("Database error")
        
        result = base_repository.delete(1)
        
        assert result is False
        mock_db.rollback.assert_called_once()
    
    def test_create_entity_success(self, base_repository, mock_db):
        """Test _create_entity creates entity successfully."""
        file_data = {
            "filename": "test.csv",
            "s3_key": "uploads/test.csv",
            "uploaded_by": 1
        }
        
        mock_file = MagicMock(spec=File)
        with patch.object(File, '__new__', return_value=mock_file):
            result = base_repository._create_entity(**file_data)
        
        assert result == mock_file
        mock_db.add.assert_called_once_with(mock_file)
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(mock_file)
    
    def test_create_entity_handles_sqlalchemy_error(self, base_repository, mock_db):
        """Test _create_entity handles SQLAlchemyError."""
        file_data = {
            "filename": "test.csv",
            "s3_key": "uploads/test.csv",
            "uploaded_by": 1
        }
        
        mock_file = MagicMock(spec=File)
        with patch.object(File, '__new__', return_value=mock_file):
            mock_db.add.side_effect = SQLAlchemyError("Database error")
            
            with pytest.raises(SQLAlchemyError):
                base_repository._create_entity(**file_data)
            
            mock_db.rollback.assert_called_once()
    
    def test_update_entity_success(self, base_repository, mock_db, sample_file):
        """Test _update_entity updates entity successfully."""
        mock_query = Mock()
        mock_filter = Mock()
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = sample_file
        mock_db.query.return_value = mock_query
        
        update_data = {"filename": "updated.csv"}
        result = base_repository._update_entity(1, update_data)
        
        assert result == sample_file
        assert hasattr(sample_file, 'filename')
        assert sample_file.filename == "updated.csv"
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(sample_file)
    
    def test_update_entity_not_found(self, base_repository, mock_db):
        """Test _update_entity returns None when entity not found."""
        mock_query = Mock()
        mock_filter = Mock()
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = None
        mock_db.query.return_value = mock_query
        
        result = base_repository._update_entity(999, {"filename": "updated.csv"})
        
        assert result is None
        mock_db.commit.assert_not_called()
    
    def test_update_entity_handles_sqlalchemy_error(self, base_repository, mock_db, sample_file):
        """Test _update_entity handles SQLAlchemyError gracefully."""
        mock_query = Mock()
        mock_filter = Mock()
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = sample_file
        mock_db.query.return_value = mock_query
        mock_db.commit.side_effect = SQLAlchemyError("Database error")
        
        update_data = {"filename": "updated.csv"}
        result = base_repository._update_entity(1, update_data)
        
        assert result is None
        mock_db.rollback.assert_called_once()
    
    def test_list_all_with_custom_order_by(self, base_repository, mock_db):
        """Test list_all with custom order_by_field."""
        mock_query = Mock()
        mock_order_by = Mock()
        mock_offset = Mock()
        mock_limit = Mock()
        
        mock_field = Mock()
        type(File).filename = mock_field
        mock_query.order_by.return_value = mock_order_by
        mock_order_by.offset.return_value = mock_offset
        mock_offset.limit.return_value = mock_limit
        mock_limit.all.return_value = []
        mock_db.query.return_value = mock_query
        
        base_repository.list_all(order_by_field="filename")
        
        mock_query.order_by.assert_called_once()

