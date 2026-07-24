from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class ResumeCriteriaItemModel(BaseModel):
    """简历评分标准项模型"""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    criterion: str = Field(description='筛选标准描述', min_length=1, max_length=500)
    weight: float = Field(default=1.0, description='该标准权重', ge=0, le=100)


class ResumeOcrResultModel(BaseModel):
    """简历OCR识别结果模型"""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    file_name: str = Field(description='原始文件名')
    saved_file_name: str = Field(description='保存后的文件名')
    storage_path: str = Field(description='文件存储绝对路径')
    ocr_text: str = Field(description='OCR识别文本')
    candidate_name: str = Field(default='', description='候选人姓名')
    candidate_email: str = Field(default='', description='候选人邮箱')
    candidate_phone: str = Field(default='', description='候选人手机号')


class ResumeScoreRequestModel(BaseModel):
    """简历评分请求模型"""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    resume_text: str = Field(description='简历文本', min_length=1)
    criteria: list[ResumeCriteriaItemModel] = Field(description='招聘筛选标准与权重')


class ResumeScoreBreakdownModel(BaseModel):
    """简历评分明细模型"""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    criterion: str = Field(description='标准描述')
    weight: float = Field(description='标准权重')
    score: float = Field(description='该项得分')
    reason: str = Field(description='打分说明')


class ResumeScoreResultModel(BaseModel):
    """简历评分结果模型"""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    score: float = Field(description='总分，范围0-100')
    summary: str = Field(description='综合评价')
    breakdown: list[ResumeScoreBreakdownModel] = Field(default_factory=list, description='评分明细')


class InterviewInviteRequestModel(BaseModel):
    """发送面试邀约请求模型"""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    candidate_name: str = Field(description='候选人姓名', min_length=1, max_length=100)
    candidate_email: str = Field(description='候选人邮箱', min_length=1, max_length=100)
    candidate_phone: str = Field(default='', description='候选人手机号', max_length=30)
    job_name: str = Field(description='岗位名称', min_length=1, max_length=120)
    hr_contact: str = Field(description='HR联系方式', min_length=1, max_length=120)
    meeting_time: str | None = Field(default=None, description='会议时间，ISO或可读字符串')


class InterviewInviteResultModel(BaseModel):
    """发送面试邀约结果模型"""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    meeting_time: str = Field(description='会议时间')
    meeting_link: str = Field(description='腾讯会议链接')
    meeting_extra_info: str = Field(default='', description='会议其余信息')
    invite_message: str = Field(description='邀约文案')
