import json
from pathlib import Path
import yaml
import pytest

DATA_DIR = Path(__file__).parent.parent / "data"

def test_code_tables_integrity():
    code_tables_path = DATA_DIR / "code_tables.json"
    assert code_tables_path.exists()
    
    with open(code_tables_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    assert "codes" in data
    codes = data["codes"]
    
    # Non-negotiable: AP15 and AP10 must be real NPCI official codes
    assert "AP15" in codes
    assert codes["AP15"]["source"] == "NPCI_OFFICIAL"
    assert codes["AP15"]["category"] == "MANDATE"
    assert "retry_mandate" in codes["AP15"]["allowed_actions"]
    
    assert "AP10" in codes
    assert codes["AP10"]["source"] == "NPCI_OFFICIAL"
    
    # Mock codes must be explicitly marked MOCK
    assert "LMS_POST_CLOSURE_DEBIT" in codes
    assert codes["LMS_POST_CLOSURE_DEBIT"]["source"] == "MOCK"
    
    assert "VKYC_NET_DROP" in codes
    assert codes["VKYC_NET_DROP"]["source"] == "MOCK"

def test_playbooks_yaml():
    playbooks_dir = DATA_DIR / "playbooks"
    assert playbooks_dir.exists()
    
    playbook_files = list(playbooks_dir.glob("*.yaml"))
    assert len(playbook_files) >= 3
    
    expected_playbooks = ["mandate_retry.yaml", "post_closure.yaml", "vkyc_resume.yaml", "disbursal_breakup.yaml"]
    for expected in expected_playbooks:
        pb_path = playbooks_dir / expected
        assert pb_path.exists()
        with open(pb_path, "r", encoding="utf-8") as f:
            content = yaml.safe_load(f)
            assert "id" in content
            assert "moment" in content
            assert "code" in content
            assert "deterministic_rules" in content
            assert "consent_spec" in content
            assert "receipt_spec" in content

def test_templates_all_languages():
    templates_dir = DATA_DIR / "templates"
    for lang in ["mr", "hi", "en"]:
        tpl_path = templates_dir / f"{lang}.json"
        assert tpl_path.exists(), f"Missing template file for {lang}"
        with open(tpl_path, "r", encoding="utf-8") as f:
            tpl_data = json.load(f)
            assert tpl_data["language"] == lang
            templates = tpl_data["templates"]
            assert "mandate_balance_failed" in templates
            assert "post_closure_debit" in templates
            assert "vkyc_dropped" in templates
            assert "disbursal_breakup" in templates
            
            # Check content
            for key, item in templates.items():
                assert "title" in item
                assert "explanation" in item
                assert "proposed_action" in item
                assert len(item["explanation"]) > 10

def test_personas_facts_and_masking():
    personas_dir = DATA_DIR / "personas"
    for persona_id in ["rohit", "asha", "sunita", "meena"]:
        p_path = personas_dir / f"{persona_id}.json"
        assert p_path.exists(), f"Missing persona {persona_id}"
        with open(p_path, "r", encoding="utf-8") as f:
            p_data = json.load(f)
            assert p_data["persona_id"] == persona_id
            assert "name" in p_data
            assert "trigger_event" in p_data
            
            # Non-negotiable rule 5: Mask PAN (show only last 4 or masked)
            pan = p_data.get("pan_masked", "")
            assert pan.startswith("XXXXX"), f"PAN for {persona_id} is not properly masked: {pan}"
            assert len(pan) == 10
