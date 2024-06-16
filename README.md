# Lightsnap
Running Lightsail instances and don't like the auto snapshot AWS provides? Run
this python module on Lambda to schedule snapshot creation with more
flexibility. By using schedule expression and the module's very own config, you
can automate snapshot creation however you like.

## INSTALL
Copy the sample config into `src`, edit it to your liking.

```sh
cp doc/config.jsonc src/config.jsonc
```

The following set up will keep max of 3 snapshots for the instance named
"Ubuntu-1".

```jsonc
{
	"boto": { // For local use. On Lambda, "the role will be assumed"
		// "region_name": "",
		// "profile_name": ""
	},
	"snapshot-instance": [
		{
			"instance-name": "Ubuntu-1",
			"prefix": "LIGHTSNAP_Ubuntu-1_", // snapshot name prefix
			"nb-copy": 3
		}
	]
}
```

### IAM Role
Create an IAM role for the Lambda function. Permissions requires in addition to
the basic execution permissions.

- GetInstanceSnapshots
- GetInstanceSnapshot
- DeleteInstanceSnapshot
- CreateInstanceSnapshot

Tip: the ARN of a Lightsail instance is made up of a randomly generated UUID
that's not exposed on the web management console. In order to get the ARN of an
instance for `CreateInstanceSnapshot` action, you need to use awscli like so.

```sh
aws lightsail get-instances
```

### Build and Upload
Run `make` to generate the layer and the function code bundle. Upload
`lambda_layer.zip` to create the layer for the function and create the Lambda
function using `lambda_function.zip` using following params:

- Runtime: **Python 3.12**
- Arch: **arm64**
- Timeout: **5 minutes** or more recommended! (AWS APIs are SLOW)

### Trigger Rule
Create a rule on EventBridge to trigger the Lambda function. The following cron
example will run the function at 16:30 UTC every other day.

```crontab
30 16 */2 * ? *
```

So in this example, if `nb-copy` is set to 3, snapshots spanning 6 days period
will be maintained.

### DONE!
Now forget that you've ever done this and move on with your life!

## Words on SNS Topic and Service Interruption
If you wish, create an SNS topic to receive notification in the event of
unsuccessful run. Errors will never occur as long as the service in your region
runs smoothly. But you may want to fire the function manually after a service
interruption. To manually run the function, use the test tab in the web
management console.

**WARNING!** Make sure you use one key-value pair otherwise the function will
run more than once, leaving you with 2 lost snapshots.
