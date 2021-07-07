from loguru import logger
import sys

logger.remove()
logger.add(sink=sys.stderr,
			format="<green>{time.hour}:{time.minute}:{time.second}:{time.microsecond}, {time.year}-{time.month}-{time.day}</green> - <lvl>{level}</lvl> - <c>{thread.name}</c> - <lvl>{message}</lvl>", 
			level="DEBUG")
logger.add('log.log', format="<green>{time.hour}:{time.minute}:{time.second}:{time.microsecond}, {time.year}-{time.month}-{time.day}</green> - <lvl>{level}</lvl> - <c>{thread.name}</c> - <lvl>{message}</lvl>", level="DEBUG")

def test():
	logger.debug('message 2')

@logger.catch
def main():
	logger.info('message')
	test()

if __name__ == '__main__':
	main()