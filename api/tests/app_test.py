#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pytest
from flask import Flask, jsonify
from backend import app

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

def test_get_data(client):
    response = client.get('/api/data/100001')
    assert response.status_code == 200
    data = response.json
    assert 'SK_ID_CURR' in data
    assert data['SK_ID_CURR'] == 100001

def test_get_data_invalid_id(client):
    response = client.get('/api/data/999999')
    assert response.status_code == 404
    data = response.json
    assert 'error' in data
    assert data['error'] == 'Client not found'


# In[ ]:




