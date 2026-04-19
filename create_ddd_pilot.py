import json, random
random.seed(42)
with open('bench/datasets/ddd_hpo.json') as f:
    data = json.load(f)
definitive = [c for c in data if c['metadata']['confidence'] == 'definitive']
strong = [c for c in data if c['metadata']['confidence'] == 'strong']
pilot = random.sample(definitive, 35) + random.sample(strong, 15)
random.shuffle(pilot)
with open('bench/datasets/ddd_hpo_pilot50.json', 'w', encoding='utf-8') as f:
    json.dump(pilot, f, ensure_ascii=False, indent=2)
print(f'Created pilot with {len(pilot)} cases')
conf = {}
for c in pilot:
    k = c['metadata']['confidence']
    conf[k] = conf.get(k, 0) + 1
print('Confidence breakdown:', conf)
print()
print('Sample case:')
c = pilot[0]
print('  id:', c['id'])
print('  diagnosis:', c['diagnoses'][0]['name'])
print('  case_en:', c['case_en'][:120])
