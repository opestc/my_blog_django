from asgiref.sync import async_to_sync
from celery import shared_task
from channels.layers import get_channel_layer
from parsel import Selector
import requests


channel_layer = get_channel_layer()


@shared_task
def add(channel_name, x, y):
	message = '{}+{}={}'.format(x, y, int(x) + int(y))
	async_to_sync(channel_layer.send)(channel_name, {"type": "chat.message", "message": message})
	print(message)
	
	
@shared_task
def search(channel_name, name, page=1):
	spider = PoemSpider(name, page)
	result = spider.parse_page()
	async_to_sync(channel_layer.send)(channel_name, {"type": "chat.message", "message": str(result)})
	print(result)
	
	
class PoemSpider(object):
	def __init__(self, *keyword):
		self.keyword = keyword[:]
		self.base_url = 'https://so.gushiwen.cn'
		self.url = self.base_url + '/search.aspx'
		
	def parse_page(self):
		params = {'value': self.keyword[0]}
		response = requests.get(self.url, params=params)
		if response.status_code == 200:
			# 创建Selector类实例
			selector = Selector(response.text)
			# 采用xpath选择器提取诗人/古籍介绍
			intro = selector.xpath('//textarea[starts-with(@id,"txtareAuthor")]/text()').get()
			content_link = selector.xpath('//div[@class="sonspic"]/div[@class="cont"]/p/a/@href').get()
			if intro:
				intro += '\n'
				content = requests.get(self.base_url + content_link)
				selector = Selector(content.text)
				titles, sentences = '', ''
				# 提取古籍目录
				if selector.xpath('//div[@class="bookcont"]/ul//span'):
					infos = selector.xpath('//div[@class="bookcont"]/ul//span')
					for info in infos:
						titles += '\n' + info.xpath('a/text()').get() + '\n'
				elif selector.xpath('//div[@class="bookcont"]'):
					infos = selector.xpath('//div[@class="bookcont"]')
					for info in infos:
						titles += '\n' + info.xpath('div[@class="bookMl"]/strong/text()').get() + '\n'
						conts = info.xpath('div[2]//span')
						for cont in conts:
							titles += '\t' + cont.xpath('a/text()').get() + '\n'
				# 提取诗人名句
				else:
					mingju_url = self.base_url + '/mingjus/default.aspx'
					params = {'astr': self.keyword[0], 'page': self.keyword[1]}
					mingju = requests.get(mingju_url, params)
					selector = Selector(mingju.text)
					words = selector.xpath('//div[@class="left"]//div[@class="cont"]')
					for word in words:
						sentences += '\n' + word.xpath('a[1]/text()').get() + ' —— ' + word.xpath('a[2]/text()').get() + '\n'
				
				if titles:
					intro += titles
				if sentences:
					intro += sentences
			# 采用xpath选择器提取诗词歌赋	
			if not intro:
				params = {'value': self.keyword[0], 'page': self.keyword[1]}
				response = requests.get(self.url, params=params)
				if response.status_code==200:
					selector = Selector(response.text) 
					infos, intro = selector.xpath('//textarea[starts-with(@id,"txtare")]'), ''
					for info in infos:
						intro += '\n'+ info.xpath('text()').get() + '\n'
			# 采用xpath选择器提取古籍章节	
			if not intro:
				try:
					chapters = selector.xpath('//div[@class="sons"]/div[@class="cont"]')
					title = chapters.xpath('.//b/text()')[0].get()
					full_link = chapters.xpath('.//@href')[1].get()
					url = self.base_url + full_link
					full_response = requests.get(url)
					# 创建Selector类实例
					if full_response.status_code==200:
						selector = Selector(full_response.text) 
						# title = selector.xpath('//h1/span/b/text()').get()
						infos, intro = selector.xpath('//div[@class="cont"]/div[@class="contson"]//p'), '\n'+title
						for info in infos:
							intro += '\n'+ info.xpath('text()').get()
				except:
					pass

			print("{}介绍:{}".format(self.keyword, intro))
			if intro:
				return intro
			
			
		print("请求失败 status:{}".format(response.status_code))
		return "未找到相关内容。"

	