"""Basic tests for Fractal Swarm"""

def test_import():
    """Test that we can import the main modules"""
    import config
    import config_solana
    assert config.config is not None
    assert config_solana.solana_config is not None

def test_version():
    """Test version file exists and is correct"""
    with open('VERSION', 'r') as f:
        version = f.read().strip()
    assert version == '1.0.0'