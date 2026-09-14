def test_database_module_imports():
    import database

    assert database.engine is not None