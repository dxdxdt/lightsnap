import datetime
import os
import sys
import time
from typing import Any, Iterable

import pyjson5
import boto3


def loadConf (path = "config.jsonc") -> dict[str, Any]:
	with open(path) as f:
		return pyjson5.load(f)

def mkBotoSession (boto):
	return boto3.session.Session(**boto)

def mkTimestampStr (ts: datetime.datetime = None) -> str:
	if ts is None:
		ts = datetime.datetime.now(datetime.UTC)
	ret = ts.isoformat()

	plus = ret.find('+')
	if plus >= 0:
		ret = ret[:plus]

	return ret.replace(':', '').replace(' ', '_')

def doSnapshotInstance (instances: Iterable[dict[str, Any]], boto = {}):
	mapped = dict([ (i["instance-name"], i) for i in instances ])
	s = mkBotoSession(boto)
	c = s.client("lightsail")

	def enumerateInstanceSnapshots () -> dict[str, list[dict[str, Any]]]:
		req_params = {}
		ret = {}

		while True:
			rsp = c.get_instance_snapshots(**req_params)
			for ss in rsp.get("instanceSnapshots"):
				i_n = ss["fromInstanceName"]
				m = mapped.get(i_n)

				if not m:
					continue
				if not ss["name"].startswith(m["prefix"]):
					continue

				l = ret.get(i_n, [])
				l.append(ss)
				ret[i_n] = l

			nt = rsp.get("nextPageToken")
			if nt:
				req_params["pageToken"] = nt
			else:
				break

		return ret

	def awaitPendingSnapshot (ss_name: str):
		rf = True

		while True:
			rsp = c.get_instance_snapshot(
				instanceSnapshotName = ss_name
			)

			if rsp["instanceSnapshot"]["state"] == "pending":
				if rf:
					sys.stderr.write(
						"Waiting for pending snapshot ..." + os.linesep)
					rf = False

				time.sleep(2.0)
			else:
				break

	def deleteInstanceSnapshots (it: Iterable[dict[str, Any]]):
		for ss in it:
			n = ss["name"]
			sys.stderr.write("Deleting: " + n + os.linesep)

			awaitPendingSnapshot(n)
			c.delete_instance_snapshot(instanceSnapshotName = n)

	# do snapshot creation requests
	for i in instances:
		instance_name = i["instance-name"]
		new_ss_name = i["prefix"] + mkTimestampStr()

		c.create_instance_snapshot(
			instanceSnapshotName = new_ss_name,
			instanceName = instance_name
		)
		sys.stderr.write("Created: " + new_ss_name + os.linesep)
		# wait for finish?

	# get the list of OUR snapshots
	ns = { i["instance-name"] for i in instances }
	ri = enumerateInstanceSnapshots()

	# rotate snapshots
	for i, l in ri.items():
		# sort by creation datetime in descending order
		l.sort(reverse = True, key = lambda e : e["createdAt"])
		nb_copy = mapped[i]["nb-copy"]
		ll = len(l)
		sys.stderr.write(i + ": " + str(ll) + " snapshots" + os.linesep)

		if ll > nb_copy:
			deleteInstanceSnapshots(l[nb_copy:])

def snapshotInstances (instances: Iterable[dict[str, Any]], boto = {}):
	doSnapshotInstance(instances, boto)

def doAll (conf: dict[str, Any]):
	snapshotInstances(conf.get("snapshot-instance"), conf.get("boto"))
