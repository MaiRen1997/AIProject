import request from "@/utils/request";

export function uploadResumeAndOcr(formData) {
  return request({
    url: "/ai/resume-filter/ocr",
    method: "post",
    headers: { "Content-Type": "multipart/form-data" },
    data: formData,
  });
}

export function scoreResumeMatch(data) {
  return request({
    url: "/ai/resume-filter/score",
    method: "post",
    data,
  });
}

export function sendInterviewInvite(data) {
  return request({
    url: "/ai/resume-filter/invite",
    method: "post",
    data,
  });
}
