from typing import Any
import json
import os
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from sqlalchemy.ext.asyncio import AsyncSession

from common.constant import CommonConstant
from common.vo import CrudResponseModel, PageModel
from exceptions.exception import ServiceException
from module_ai.dao.product_info_dao import Product_infoDao
from module_ai.dao.product_equipment_dao import Product_equipmentDao
from module_ai.entity.vo.product_info_vo import Product_infoPageQueryModel
from module_ai.entity.vo.product_equipment_vo import DeleteProduct_equipmentModel, Product_equipmentModel, Product_equipmentPageQueryModel
from utils.common_util import CamelCaseUtil
from utils.excel_util import ExcelUtil


class Product_equipmentService:
    """
    产品组件模块服务层
    """

    @classmethod
    async def get_product_equipment_list_services(
        cls, query_db: AsyncSession, query_object: Product_equipmentPageQueryModel, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        """
        获取产品组件列表信息service

        :param query_db: orm对象
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 产品组件列表信息对象
        """
        product_equipment_list_result = await Product_equipmentDao.get_product_equipment_list(query_db, query_object, is_page)

        return product_equipment_list_result


    @classmethod
    async def add_product_equipment_services(cls, query_db: AsyncSession, page_object: Product_equipmentModel) -> CrudResponseModel:
        """
        新增产品组件信息service

        :param query_db: orm对象
        :param page_object: 新增产品组件对象
        :return: 新增产品组件校验结果
        """
        try:
            await Product_equipmentDao.add_product_equipment_dao(query_db, page_object)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def edit_product_equipment_services(cls, query_db: AsyncSession, page_object: Product_equipmentModel) -> CrudResponseModel:
        """
        编辑产品组件信息service

        :param query_db: orm对象
        :param page_object: 编辑产品组件对象
        :return: 编辑产品组件校验结果
        """
        edit_product_equipment = page_object.model_dump(exclude_unset=True, exclude={})
        product_equipment_info = await cls.product_equipment_detail_services(query_db, page_object.id)
        if product_equipment_info.id:
            try:
                await Product_equipmentDao.edit_product_equipment_dao(query_db, edit_product_equipment)
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='更新成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='产品组件不存在')

    @classmethod
    async def delete_product_equipment_services(cls, query_db: AsyncSession, page_object: DeleteProduct_equipmentModel) -> CrudResponseModel:
        """
        删除产品组件信息service

        :param query_db: orm对象
        :param page_object: 删除产品组件对象
        :return: 删除产品组件校验结果
        """
        if page_object.ids:
            id_list = page_object.ids.split(',')
            try:
                for id in id_list:
                    await Product_equipmentDao.delete_product_equipment_dao(query_db, Product_equipmentModel(id=id))
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='删除成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='传入id唯一标识为空')

    @classmethod
    async def product_equipment_detail_services(cls, query_db: AsyncSession, id: int) -> Product_equipmentModel:
        """
        获取产品组件详细信息service

        :param query_db: orm对象
        :param id: id唯一标识
        :return: id唯一标识对应的信息
        """
        product_equipment = await Product_equipmentDao.get_product_equipment_detail_by_id(query_db, id=id)
        result = Product_equipmentModel(**CamelCaseUtil.transform_result(product_equipment)) if product_equipment else Product_equipmentModel()

        return result

    @staticmethod
    async def export_product_equipment_list_services(product_equipment_list: list) -> bytes:
        """
        导出产品组件信息service

        :param product_equipment_list: 产品组件信息列表
        :return: 产品组件信息对应excel的二进制数据
        """
        # 创建一个映射字典，将英文键映射到中文键
        mapping_dict = {
            'id': 'id唯一标识',
            'productName': '备件名称',
            'productNo': '备件号',
            'priceIncludingTax': '含税价',
            'purchasePrice': '进货价',
        }
        binary_data = ExcelUtil.export_list2excel(product_equipment_list, mapping_dict)

        return binary_data

    @classmethod
    async def _extract_product_from_input(cls, query_db: AsyncSession, user_input: str) -> tuple[str, str]:
        """
        使用AI从用户输入中提取产品名称和产品号(型号)

        :param query_db: orm对象
        :param user_input: 用户输入
        :return: (产品名称, 产品号)
        """
        user_input = (user_input or '').strip()
        if not user_input:
            raise ServiceException(message='输入内容不能为空')

        api_key, base_url, model = cls._resolve_deepseek_llm_config()
        url = cls._resolve_chat_completions_url(base_url)
        prompt = (
            '请从用户输入中提取“产品名称”和“型号(即产品号)”。\\n'
            '必须仅输出JSON对象，禁止输出任何解释性文本。\\n'
            'JSON格式严格为: {"productName":"", "productNo":""}\\n'
            f'用户输入: {user_input}'
        )
        request_body = {
            'model': model,
            'messages': [
                {'role': 'system', 'content': '你是信息抽取助手，只返回JSON对象。'},
                {'role': 'user', 'content': prompt},
            ],
            'temperature': 0,
            'max_tokens': 256,
        }
        req = Request(
            url,
            data=json.dumps(request_body, ensure_ascii=False).encode('utf-8'),
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
            },
            method='POST',
        )

        try:
            with urlopen(req, timeout=120) as resp:
                response_bytes = resp.read()
        except HTTPError as e:
            err_text = e.read().decode('utf-8', errors='ignore') if hasattr(e, 'read') else str(e)
            raise ServiceException(message=f'AI提取产品信息失败: HTTP {e.code}, {err_text}') from e
        except URLError as e:
            raise ServiceException(message=f'AI提取产品信息失败: 无法连接模型服务, {e}') from e
        except Exception as e:
            raise ServiceException(message=f'AI提取产品信息失败: {e}') from e

        try:
            payload = json.loads(response_bytes.decode('utf-8'))
        except Exception as e:
            raise ServiceException(message='AI提取产品信息失败: 上游返回无法解析') from e

        choices = payload.get('choices') if isinstance(payload, dict) else None
        if not isinstance(choices, list) or not choices:
            raise ServiceException(message=f'AI提取产品信息失败: 未返回有效结果, response={payload}')

        message = choices[0].get('message') if isinstance(choices[0], dict) else None
        full_response = message.get('content') if isinstance(message, dict) else None
        if not full_response:
            raise ServiceException(message='AI提取产品信息失败: 未返回内容')

        product_name = ''
        product_no = ''
        if full_response:
            json_text = full_response.strip()
            match = re.search(r'\{[\s\S]*\}', json_text)
            if match:
                json_text = match.group(0)
            try:
                parsed = json.loads(json_text)
                product_name = str(parsed.get('productName') or '').strip()
                product_no = str(parsed.get('productNo') or '').strip()
            except Exception:
                product_name = ''
                product_no = ''

        # AI解析失败时的兜底策略，尽量从自然语言中抓取关键字
        if not product_name:
            name_match = re.search(r'(?:产品名称|名称)\s*[:：]\s*([^,，;；\\n]+)', user_input)
            if name_match:
                product_name = name_match.group(1).strip()
        if not product_no:
            no_match = re.search(r'(?:型号|产品号|productNo)\s*[:：]\s*([^,，;；\\n]+)', user_input)
            if no_match:
                product_no = no_match.group(1).strip()

        if not product_name or not product_no:
            raise ServiceException(message='无法从输入中提取产品名称和型号，请按“产品名称:xxx, 型号:yyy”输入')

        return product_name, product_no

    @classmethod
    def _resolve_deepseek_llm_config(cls) -> tuple[str, str, str]:
        """
        解析 DeepSeek 配置

        :return: (api_key, base_url, model)
        """
        api_key = os.getenv('DEEPSEEK_API_KEY', '').strip()
        if not api_key:
            raise ServiceException(message='未配置 DEEPSEEK_API_KEY，无法提取产品信息')

        base_url = os.getenv('DEEPSEEK_API_BASE_URL', '').strip() or 'https://api.deepseek.com/v1'
        model = os.getenv('DEEPSEEK_CHAT_MODEL', '').strip() or os.getenv('AI_CHAT_MODEL', '').strip() or 'deepseek-chat'
        return api_key, base_url, model

    @classmethod
    def _resolve_chat_completions_url(cls, base_url: str) -> str:
        """
        兼容 base_url 的不同格式，规范为 /v1/chat/completions

        :param base_url: 基础URL
        :return: chat completions url
        """
        normalized = (base_url or '').strip().rstrip('/')
        parsed = urlparse(normalized)
        path = parsed.path.rstrip('/')

        if path.endswith('/chat/completions'):
            return normalized
        if path.endswith('/v1'):
            return f'{normalized}/chat/completions'
        if '/v1/' in f'{path}/':
            base_root = normalized.split('/v1/', maxsplit=1)[0]
            return f'{base_root}/v1/chat/completions'
        return f'{normalized}/v1/chat/completions'

    @classmethod
    def _parse_relation_eqp_ids(cls, relation_eqp_id: str | None) -> list[int]:
        """
        将relationEqpId按逗号拆分并转换为id列表

        :param relation_eqp_id: 关联组件id字符串
        :return: 组件id列表
        """
        if not relation_eqp_id:
            return []
        id_list: list[int] = []
        for raw in relation_eqp_id.split(','):
            value = raw.strip()
            if not value:
                continue
            if value.isdigit():
                id_list.append(int(value))
        return id_list

    @classmethod
    async def _resolve_give_price_rows(
        cls,
        query_db: AsyncSession,
        user_input: str,
    ) -> tuple[str, str, list[dict[str, Any]]]:
        """
        根据用户输入解析产品并查询配件明细

        :param query_db: orm对象
        :param user_input: 用户输入文本
        :return: (产品名称, 产品型号, 配件明细行)
        """
        product_name, product_no = await cls._extract_product_from_input(query_db, user_input)

        product_query = Product_infoPageQueryModel(
            product_name=product_name,
            product_no=product_no,
            page_num=1,
            page_size=100,
        )
        product_list = await Product_infoDao.get_product_info_list(query_db, product_query, is_page=False)

        if not product_list:
            product_query.product_no = None
            product_list = await Product_infoDao.get_product_info_list(query_db, product_query, is_page=False)

        if not product_list:
            raise ServiceException(message=f'未找到产品，产品名称={product_name}，型号={product_no}')

        target_product = None
        for product in product_list:
            product_no_value = str(product.get('productNo') or '')
            if product_no_value == product_no:
                target_product = product
                break
        if not target_product:
            target_product = product_list[0]

        relation_eqp_id = target_product.get('relationEqpId')
        eqp_id_list = cls._parse_relation_eqp_ids(relation_eqp_id)
        if not eqp_id_list:
            raise ServiceException(message='该产品未配置relationEqpId或格式不正确，无法查询配件')

        equipment_list = await Product_equipmentDao.get_product_equipment_list_by_ids(query_db, eqp_id_list)
        equipment_map = {int(item.id): item for item in equipment_list}

        rows: list[dict[str, Any]] = []
        for eqp_id in eqp_id_list:
            eqp = equipment_map.get(eqp_id)
            if not eqp:
                continue
            rows.append(
                {
                    'productName': target_product.get('productName'),
                    'productNo': target_product.get('productNo'),
                    'equipmentId': eqp.id,
                    'equipmentName': eqp.product_name,
                    'equipmentNo': eqp.product_no,
                    'priceBeforeTax': eqp.price_including_tax,
                    'purchasePrice': eqp.purchase_price,
                }
            )

        if not rows:
            raise ServiceException(message='未查询到有效配件信息，请检查relationEqpId配置')

        return product_name, product_no, rows

    @classmethod
    def _build_markdown_table(cls, rows: list[dict[str, Any]]) -> str:
        """
        将明细行转换为markdown表格

        :param rows: 明细行
        :return: markdown表格
        """
        headers = ['产品名称', '产品型号', '配件ID', '配件名称', '配件号', '税前价格', '购买价格']
        lines = [
            '| ' + ' | '.join(headers) + ' |',
            '| ' + ' | '.join(['---'] * len(headers)) + ' |',
        ]
        for row in rows:
            lines.append(
                '| '
                + ' | '.join(
                    [
                        str(row.get('productName') or ''),
                        str(row.get('productNo') or ''),
                        str(row.get('equipmentId') or ''),
                        str(row.get('equipmentName') or ''),
                        str(row.get('equipmentNo') or ''),
                        str(row.get('priceBeforeTax') or ''),
                        str(row.get('purchasePrice') or ''),
                    ]
                )
                + ' |'
            )
        return '\n'.join(lines)

    @classmethod
    def _parse_markdown_table(cls, markdown_content: str) -> list[dict[str, Any]]:
        """
        将markdown表格解析为导出行数据

        :param markdown_content: markdown表格文本
        :return: 导出行
        """
        text = (markdown_content or '').strip()
        if not text:
            raise ServiceException(message='markdown内容为空，无法导出')

        lines = [line.strip() for line in text.splitlines() if line.strip() and '|' in line]
        if len(lines) < 3:
            raise ServiceException(message='markdown表格格式不正确，无法导出')

        def split_row(row_text: str) -> list[str]:
            raw_cells = row_text.split('|')
            if len(raw_cells) >= 2:
                raw_cells = raw_cells[1:-1]
            return [cell.strip() for cell in raw_cells]

        header_cells = split_row(lines[0])
        valid_header = ['产品名称', '产品型号', '配件ID', '配件名称', '配件号', '税前价格', '购买价格']
        if header_cells != valid_header:
            raise ServiceException(message='markdown表头不匹配，无法导出')

        export_rows: list[dict[str, Any]] = []
        for line in lines[2:]:
            # 跳过分隔线误入情况
            if re.fullmatch(r'\|?\s*[-:|\s]+\|?', line):
                continue
            cells = split_row(line)
            if len(cells) != 7:
                continue
            export_rows.append(
                {
                    'productName': cells[0],
                    'productNo': cells[1],
                    'equipmentId': cells[2],
                    'equipmentName': cells[3],
                    'equipmentNo': cells[4],
                    'priceBeforeTax': cells[5],
                    'purchasePrice': cells[6],
                }
            )

        if not export_rows:
            raise ServiceException(message='markdown表格无有效数据，无法导出')

        return export_rows

    @classmethod
    async def query_give_price_chat_services(cls, query_db: AsyncSession, user_input: str) -> dict[str, Any]:
        """
        givePriceChat查询：输入文本 -> AI提取产品 -> 查主表和子表 -> 返回markdown

        :param query_db: orm对象
        :param user_input: 用户输入文本
        :return: 查询结果
        """
        product_name, product_no, rows = await cls._resolve_give_price_rows(query_db, user_input)
        markdown_table = cls._build_markdown_table(rows)

        return {
            'productName': product_name,
            'productNo': product_no,
            'rows': rows,
            'markdownTable': markdown_table,
        }

    @classmethod
    async def export_give_price_chat_services(cls, query_db: AsyncSession, user_input: str) -> bytes:
        """
        givePriceChat专用导出：输入文本 -> AI提取产品 -> 查主表和子表 -> 导出excel

        :param query_db: orm对象
        :param user_input: 用户输入文本
        :return: excel二进制数据
        """
        _, _, export_rows = await cls._resolve_give_price_rows(query_db, user_input)

        mapping_dict = {
            'productName': '产品名称',
            'productNo': '产品型号',
            'equipmentId': '配件ID',
            'equipmentName': '配件名称',
            'equipmentNo': '配件号',
            'priceBeforeTax': '税前价格',
            'purchasePrice': '购买价格',
        }

        return ExcelUtil.export_list2excel(export_rows, mapping_dict)

    @classmethod
    async def export_give_price_chat_markdown_services(cls, markdown_content: str) -> bytes:
        """
        givePriceChat专用导出：markdown表格 -> excel

        :param markdown_content: markdown表格
        :return: excel二进制数据
        """
        export_rows = cls._parse_markdown_table(markdown_content)

        mapping_dict = {
            'productName': '产品名称',
            'productNo': '产品型号',
            'equipmentId': '配件ID',
            'equipmentName': '配件名称',
            'equipmentNo': '配件号',
            'priceBeforeTax': '税前价格',
            'purchasePrice': '购买价格',
        }

        return ExcelUtil.export_list2excel(export_rows, mapping_dict)
