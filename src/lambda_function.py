import lightsnap


conf = lightsnap.loadConf()

def lambda_handler (event, context):
	global conf

	lightsnap.doAll(conf)
