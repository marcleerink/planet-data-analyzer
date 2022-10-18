from modules.importer.api_importer import handle_exception, RateLimitException, search_requester


# def test_handle_exception(requests_mock):
#     assert handle_exception(response) == RateLimitException("Rate limit error")
#     assert handle_exception(300) == Exception 


def test_search_requester():
    geometry = {'type': 'Polygon', 'coordinates': [[[12.463552, 52.169746], [12.463552, 52.862511], [14.305487, 52.862511], [14.305487, 52.169746], [12.463552, 52.169746]]]}
    result = {'item_types': ['PSScene','SkySatScene'],
        'filter': {'type': 'AndFilter', 
        'config': [{'type': 'DateRangeFilter', 'field_name': 'acquired', 
        'config': {'gte': '2022-10-01T00:00:00.000Z', 'lte': '2022-10-02T00:00:00.000Z'}}, 
        {'type': 'RangeFilter', 'field_name': 'cloud_cover', 'config': {'lte': 0.3}}, 
        {'type': 'GeometryFilter', 'field_name': 'geometry', 
        'config': {'type': 'Polygon', 'coordinates': 
        [[[12.463552, 52.169746], [12.463552, 52.862511], [14.305487, 52.862511], [14.305487, 52.169746], [12.463552, 52.169746]]]}}]}}
    assert search_requester(item_types=['PSScene', 'SkySatScene'],
                                    start_date='2022-10-01',
                                    end_date='2022-10-02',
                                    cc = 0.3,
                                    geometry=geometry) == result
    