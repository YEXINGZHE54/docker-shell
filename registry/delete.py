#!/usr/bin/env python3

import requests as req
from urllib.parse import urlparse, parse_qs

def sortfn(tag):
	fields = tag.split("-")
	if len(fields) < 2:
		return 0
	val = 0
	try:
		val = int(fields[-1])
	except Exception:
		val = 0
	return val

def pages(make_req, parse_response):
	last = ""
	while True:
		print("current last: {}".format(last))
		resp = make_req(last)
		if resp.status_code != 200:
			return resp.status_code
		ctue = parse_response(resp)
		if not ctue:
			break # should not continue
		link = resp.headers.get("Link", "")
		if link == "":
			break # done
		print("got link: {}".format(link))
		fields = link.split(";")
		u = urlparse(fields[0])
		args = parse_qs(u.query)
		lastvals = args.get("last", [])
		print("got last: {}".format(lastvals))
		if len(lastvals) == 0 or lastvals[0] == "":
			return -1 # invalid args
		last = lastvals[0]
	return 200

def get_repos(registry, user, password):
	result = []
	def makereq(last):
		dest = registry + "/v2/_catalog?n=100"
		if last != "":
			dest = "{}&last={}".format(dest, last)
		print("calling url {}".format(dest))
		return req.get(dest, auth=(user, password))

	def response(resp):
		res = resp.json()
		result.extend(res.get("repositories", []))
		return True

	code = pages(makereq, response)
	if code != 200:
		print("failed to load repos, code: {}".format(code))
	return result

def get_images(registry, user, password, repo):
	result = []
	def makereq(last):
		dest = registry + "/v2/{}/tags/list?n=100".format(repo)
		if last != "":
			dest = "{}&last={}".format(dest, last)
		print("calling url {}".format(dest))
		return req.get(dest, auth=(user, password))

	def response(resp):
		res = resp.json()
		data = res.get("tags", None)
		if type(data) is list:
			result.extend(data)
		return True

	code = pages(makereq, response)
	if code != 200:
		print("failed to load images, code: {}".format(code))
	return result

def get_image_digest(registry, user, password, repo, tag):
	dest = registry + "/v2/{}/manifests/{}".format(repo, tag)
	resp = req.head(dest, auth=(user, password), headers={"Accept": "application/vnd.docker.distribution.manifest.v2+json"})
	if resp.status_code != 200:
		print("failed to load digest for {}:{}, code: {}, reason: {}".format(repo, tag, resp.status_code, resp.reason))
		return ""
	return resp.headers.get("Docker-Content-Digest", "")

def delete_image(registry, user, password, repo, digest):
	dest = registry + "/v2/{}/manifests/{}".format(repo, digest)
	resp = req.delete(dest, auth=(user, password), headers={"Accept": "application/vnd.docker.distribution.manifest.v2+json"})
	if resp.status_code != 202:
		print("failed to delete digest for {}:{}, code: {}, reason: {}".format(repo, digest, resp.status_code, resp.reason))
		return False
	return True

def clean_repos(registry, user, password, repo):
	images = get_images(registry, user, password, repo)
	images = sorted(images, key = sortfn)
	for img in images[:-1]: # skip last one
		digest = get_image_digest(registry, user, password, repo, img)
		if digest == "":
			continue # skipped
		print("got digest {}".format(digest))
		delete_image(registry, user, password, repo, digest)
		print("delete image {}:{} done".format(repo, img))

	return

def main():
	registry = "http://$host:$port"
	user = "user"
	password = "password"

	repos = get_repos(registry, user, password)
	for repo in repos:
		if not repo.startswith("develop"):
			print("repo {} not starting with develop, it was skipped!".format(repo))
			continue
		clean_repos(registry, user, password, repo)
		print("clean repo {} done".format(repo))

	print("done")

if __name__ == '__main__':
	main()
