from django.http import HttpResponse
from elasticsearch import Elasticsearch
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import json


@csrf_exempt
def index(request, name):
    if request.method != 'GET' and request.method != 'POST':
        return HttpResponse("This method is not allowed!\n")
    if name != 'file' and name != 'organism' and name != 'specimen' and name != 'dataset':
        return HttpResponse("This method is not allowed!\n")
    size = request.GET.get('size', 10)
    es = Elasticsearch([settings.NODE1, settings.NODE2])
    if request.body:
        results = es.search(index=name, size=size, body=json.loads(request.body))
    else:
        field = request.GET.get('_source', '')
        sort = request.GET.get('sort', '')
        query = request.GET.get('q', '')
        if query != '':
            results = es.search(index=name, size=size, _source=field, sort=sort, q=query)
        else:
            results = es.search(index=name, size=size, _source=field, sort=sort)
    results = json.dumps(results)
    return HttpResponse(results)


@csrf_exempt
def detail(request, name, id):
    if request.method != 'GET':
        return HttpResponse("This method is not allowed!\n")
    es = Elasticsearch([settings.NODE1, settings.NODE2])
    results = es.search(index=name, q="_id:{}".format(id))
    if results['hits']['total'] == 0:
        results = es.search(index=name, q="alternativeId:{}".format(id))
    results = json.dumps(results)
    return HttpResponse(results)


@csrf_exempt
def get_protocols(request):
    es = Elasticsearch([settings.NODE1, settings.NODE2])
    results = es.search(index="specimen", size=100000)
    entries = {}
    for result in results["hits"]["hits"]:
        if "specimenFromOrganism" in result["_source"]:
            key = result['_source']['specimenFromOrganism']['specimenCollectionProtocol']['filename']
            parsed = key.split("_")
            if parsed[0] in settings.UNIVERSITIES:
                name = settings.UNIVERSITIES[parsed[0]]
                protocol_name = " ".join(parsed[2:-1])
                date = parsed[-1].split(".")[0]
                entries.setdefault(key, {"specimen": [], "organism": [], "name": "", "date": "", "protocol_name": ""})
                entries[key]["specimen"].append(result["_id"])
                entries[key]["organism"].append(result["_source"]["derivedFrom"])
                entries[key]['name'] = name
                entries[key]['date'] = date
                entries[key]["protocol_name"] = protocol_name
    results = json.dumps(list(entries.values()))
    return HttpResponse(results)
