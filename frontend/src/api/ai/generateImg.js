import request from "@/utils/request";

export function generateTextToImage(data) {
  return request({
    url: "/ai/generate-img/text-to-image",
    method: "post",
    data,
  });
}
