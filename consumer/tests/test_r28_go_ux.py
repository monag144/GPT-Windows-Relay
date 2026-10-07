from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import consumer_app as ca

class V:
    def __init__(self,v): self.v=v
    def get(self): return self.v
class E:
    def __init__(self,state=0): self.state=state
class T:
    def __init__(self,text): self.value=text; self.deleted=False
    def get(self,*_): return self.value
    def delete(self,*_): self.value=''; self.deleted=True

def test_send_on_enter_off_keeps_newline_behavior():
    x=object.__new__(ca.ConsumerApp); x.send_on_enter=V(False); x.go=lambda: (_ for _ in ()).throw(AssertionError('go called'))
    assert ca.ConsumerApp._text_return(x,E()) is None

def test_send_on_enter_on_goes_but_shift_enter_does_not():
    x=object.__new__(ca.ConsumerApp); x.send_on_enter=V(True); called=[]; x.go=lambda: called.append(True)
    assert ca.ConsumerApp._text_return(x,E())=='break'; assert called==[True]
    called.clear(); assert ca.ConsumerApp._text_return(x,E(1)) is None; assert called==[]

def test_clear_only_when_editor_still_contains_sent_mission():
    x=object.__new__(ca.ConsumerApp); x.text=T('hello\n'); ca.ConsumerApp._clear_mission_if_unchanged(x,'hello'); assert x.text.deleted
    x.text=T('edited'); ca.ConsumerApp._clear_mission_if_unchanged(x,'hello'); assert not x.text.deleted

def test_r28_source_contracts():
    text=(ROOT/'consumer_app.py').read_text(encoding='utf-8'); assert 'Send on Enter' in text; assert 'send_on_enter' in text; assert '_clear_mission_if_unchanged' in text
