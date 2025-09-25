from reporting._stubs.designer_template import sanitise_template_in_place


def test_sanitise_template_in_place_removes_unrecognised_parameter_fields():
    template = {
        "parameters": [
            {
                "id": 1,
                "name": "title",
                "type": "string",
                "label": "Título",
                "testData": "Ficha",
            }
        ]
    }

    sanitise_template_in_place(template)

    assert template["parameters"] == [
        {
            "id": 1,
            "name": "title",
            "type": "string",
            "testData": "Ficha",
        }
    ]


def test_sanitise_template_in_place_handles_missing_parameters():
    template: dict[str, object] = {"parameters": ["not-a-mapping"]}

    sanitise_template_in_place(template)

    assert template["parameters"] == []


def test_sanitise_template_in_place_ignores_non_dict_templates():
    sanitise_template_in_place(None)
    template: dict[str, object] = {}
    sanitise_template_in_place(template)
    assert template == {}
