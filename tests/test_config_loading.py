def test_config_loading():
    from config import Config

    config = Config.load_from_env()
    assert config.api_key, "API key missing"
    assert config.db_file_path, "DB path missing"
    assert isinstance(config.logger, object), "Logger not initialized"