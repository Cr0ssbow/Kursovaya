from database.models import UserLog, db
from datetime import datetime, timedelta

def cleanup_old_logs(days_to_keep=90, auth_manager=None):
    """
    Удаляет логи старше указанного количества дней
    
    Args:
        days_to_keep (int): Количество дней для хранения логов (по умолчанию 90)
        auth_manager: Менеджер авторизации для логирования
    """
    try:
        if db.is_closed():
            db.connect()
        
        # Вычисляем дату, старше которой нужно удалить логи
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        # Логируем операцию очистки перед удалением
        if auth_manager:
            auth_manager.log_action("Очистка старых логов", f"Начата очистка логов старше {days_to_keep} дней")
        
        # Удаляем старые логи, исключая записи об очистке логов
        deleted_count = UserLog.delete().where(
            (UserLog.created_at < cutoff_date) & 
            (~UserLog.action.contains("Очистка старых логов"))
        ).execute()
        
        # Логируем результат
        if auth_manager:
            auth_manager.log_action("Очистка старых логов", f"Удалено {deleted_count} записей логов старше {days_to_keep} дней")
        
        print(f"Удалено {deleted_count} старых записей логов (старше {days_to_keep} дней)")
        return deleted_count
        
    except Exception as e:
        print(f"Ошибка при очистке логов: {e}")
        return 0
    finally:
        if not db.is_closed():
            db.close()

def get_logs_statistics():
    """
    Возвращает статистику по логам
    
    Returns:
        dict: Словарь со статистикой
    """
    try:
        if db.is_closed():
            db.connect()
        
        total_logs = UserLog.select().count()
        
        # Логи за последние 30 дней
        thirty_days_ago = datetime.now() - timedelta(days=30)
        recent_logs = UserLog.select().where(UserLog.created_at >= thirty_days_ago).count()
        
        # Самый старый лог
        oldest_log = UserLog.select().order_by(UserLog.created_at.asc()).first()
        oldest_date = oldest_log.created_at if oldest_log else None
        
        # Самый новый лог
        newest_log = UserLog.select().order_by(UserLog.created_at.desc()).first()
        newest_date = newest_log.created_at if newest_log else None
        
        return {
            'total_logs': total_logs,
            'recent_logs': recent_logs,
            'oldest_date': oldest_date,
            'newest_date': newest_date
        }
        
    except Exception as e:
        print(f"Ошибка при получении статистики логов: {e}")
        return {
            'total_logs': 0,
            'recent_logs': 0,
            'oldest_date': None,
            'newest_date': None
        }
    finally:
        if not db.is_closed():
            db.close()

if __name__ == "__main__":
    # Пример использования
    stats = get_logs_statistics()
    print(f"Всего логов: {stats['total_logs']}")
    print(f"Логов за последние 30 дней: {stats['recent_logs']}")
    
    if stats['oldest_date']:
        print(f"Самый старый лог: {stats['oldest_date'].strftime('%d.%m.%Y %H:%M:%S')}")
    if stats['newest_date']:
        print(f"Самый новый лог: {stats['newest_date'].strftime('%d.%m.%Y %H:%M:%S')}")
    
    # Очистка логов старше 90 дней
    cleanup_old_logs(90)