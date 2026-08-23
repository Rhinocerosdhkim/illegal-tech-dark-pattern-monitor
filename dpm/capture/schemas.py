from typing import Optional, List, Union, Literal
from pydantic import BaseModel, Field

class Signal(BaseModel):
    value: Union[bool, int, float, str]
    step: str
    evidence: str

class SignalEntry(BaseModel):
    name: str = Field(..., description="The exact metric name (e.g., 'banner_detected', 'order_button_label')")
    signal: Signal

class SignalErrorEntry(BaseModel):
    name: str = Field(..., description="The exact metric name that failed evaluation")
    reason: str = Field(..., description="The English justification for why it could not be evaluated")

class UnifiedDecision(BaseModel):
    thought_process: str = Field(..., description="Your reasoning for both the audit findings and the next action.")
    
    # Audit Findings for this step
    signals: List[SignalEntry] = Field(default_factory=list, description="Raw UI signals extracted from this current screenshot.")
    signal_errors: List[SignalErrorEntry] = Field(default_factory=list, description="Signals that could not be evaluated in this step.")

    # Navigation Action
    action_type: Literal["click", "double_click", "right_click", "hover", "type", "key", "scroll", "wait", "drag_and_drop", "click_pixel", "double_click_pixel", "right_click_pixel", "hover_pixel", "drag_pixel", "none"] = Field(
        ..., 
        description="The next action to take to progress through the funnel."
    )
    target_id: Optional[int] = Field(None, description="The ID of the element to interact with.")
    target_pixel: Optional[List[int]] = Field(None, description="[x, y] in 0-1000 coordinates.")
    drag_pixels: Optional[List[List[int]]] = Field(None, description="[[start_x, start_y], [end_x, end_y]] in 0-1000 coordinates.")
    input_text: Optional[str] = Field(None, description="Text for 'type', key name for 'key', direction for 'scroll', or duration for 'wait'.")
    
    goal_reached: bool
    is_blocked: bool = Field(False)
    step_name: str = Field(..., description="Logical name for this step (e.g., 'cookie_asymmetry_check').")
