import unittest
import itertools
import random

import config.parse

class ExecutableNameTests(unittest.TestCase):

    def test_last_executable_takes_priority(self):
        a = { 'executable_name': 'a' }
        b = { 'executable_name': 'b' }
        self.assertEqual(config.parse.executable_name(a,b), b['executable_name'])

    def test_combine_names(self):
        a = { 'name': 'a' }
        b = { 'name': 'b' }
        self.assertEqual(config.parse.executable_name(a,b), 'champsim_a_b')

    def test_combine_names_skips_missing(self):
        a = {}
        b = { 'name': 'b' }
        self.assertEqual(config.parse.executable_name(a,b), 'champsim_b')
        self.assertEqual(config.parse.executable_name(b,a), 'champsim_b')

    def test_combine_names_empty(self):
        a = {}
        b = {}
        self.assertEqual(config.parse.executable_name(a,b), 'champsim')
        self.assertEqual(config.parse.executable_name(b,a), 'champsim')

    def test_executable_over_names(self):
        a = { 'name': 'a' }
        b = { 'name': 'b', 'executable_name': 'b_exec' }
        self.assertEqual(config.parse.executable_name(a,b), 'b_exec')
        self.assertEqual(config.parse.executable_name(b,a), 'b_exec')

class DuplicateToLengthTests(unittest.TestCase):

    def test_length(self):
        for i in range(1,10,2):
            with self.subTest(i=i):
                self.assertEqual(len(config.parse.duplicate_to_length([{}], i)), i)

    def test_duplication(self):
        a = { 'name': 'a' }
        self.assertEqual(config.parse.duplicate_to_length([a], 2), [a]*2)
        self.assertEqual(config.parse.duplicate_to_length([a], 4), [a]*4)
        self.assertEqual(config.parse.duplicate_to_length([a], 8), [a]*8)

    def test_grouped_duplication(self):
        a = { 'name': 'a' }
        b = { 'name': 'b' }
        self.assertEqual(config.parse.duplicate_to_length([a,b], 4), [a,a,b,b])
        self.assertEqual(config.parse.duplicate_to_length([a,b], 5), [a,a,a,b,b])
        self.assertEqual(config.parse.duplicate_to_length([a,b], 6), [a,a,a,b,b,b])

    def test_truncate(self):
        a = { 'name': 'a' }
        b = { 'name': 'b' }
        c = { 'name': 'c' }
        self.assertEqual(config.parse.duplicate_to_length([a,b,c], 2), [a,b])

class SplitStringOrListTests(unittest.TestCase):

    def test_empty_string(self):
        self.assertEqual(config.parse.split_string_or_list(''), [])

    def test_empty_list(self):
        self.assertEqual(config.parse.split_string_or_list([]), [])

    def test_list_passthrough(self):
        self.assertEqual(config.parse.split_string_or_list(['a','b']), ['a','b'])

    def test_string_split(self):
        self.assertEqual(config.parse.split_string_or_list('a,b'), ['a','b'])

    def test_string_strip(self):
        self.assertEqual(config.parse.split_string_or_list('a, b'), ['a','b'])

class FilterInaccessibleTests(unittest.TestCase):

    def test_empty_system(self):
        self.assertEqual(len(config.parse.filter_inaccessible({}, ['a', 'b'])), 0)

    def test_empty_roots(self):
        system = {
                'a' : { 'name': 'a', 'lower_level': 'b' },
                'b' : { 'name': 'b', 'lower_level': 'c' },
                'c' : { 'name': 'c', 'lower_level': 'd' }
                }
        self.assertEqual(len(config.parse.filter_inaccessible(system, [])), 0)

    def test_coincident_roots(self):
        system = {
                'a' : { 'name': 'a', 'lower_level': 'b' },
                'b' : { 'name': 'b', 'lower_level': 'c' },
                'c' : { 'name': 'c', 'lower_level': 'd' }
                }
        result = config.parse.filter_inaccessible(system, ['a','b'])
        self.assertCountEqual(system, result)

    def test_coincident_roots(self):
        system = {
                'a' : { 'name': 'a', 'lower_level': 'b' },
                'b' : { 'name': 'b', 'lower_level': 'c' },
                'c' : { 'name': 'c', 'lower_level': 'd' },
                'orphan' : { 'name': 'orphan', 'lower_level': 'd' }
                }
        result = config.parse.filter_inaccessible(system, ['a'])
        self.assertEqual(len(result), 3)
        self.assertIn('a', result)
        self.assertIn('b', result)
        self.assertIn('c', result)

class PassthroughContext:
    def find(self, module):
        return {'name': module, 'fname': 'xxyzzy/'+module, '_is_instruction_prefetcher': module.endswith('_instr')}

    def find_all(self):
        return [] # FIXME

class ParseNormalizedTests(unittest.TestCase):

    def test_generates_default_caches(self):
        config_cores = [{ 'name': 'test_cpu' }]

        for key in ('L1I', 'L1D', 'ITLB', 'DTLB'):
            with self.subTest(cache=key):
                result = config.parse.parse_normalized(config_cores, {}, {}, {}, {}, {}, PassthroughContext(), PassthroughContext(), PassthroughContext(), PassthroughContext(), False)
                cache_name = result[0]['cores'][0][key]
                caches = result[0]['caches']

                self.assertIn(cache_name, [c['name'] for c in caches])

    def test_generates_default_ptws(self):
        config_cores = [{ 'name': 'test_cpu' }]

        result = config.parse.parse_normalized(config_cores, {}, {}, {}, {}, {}, PassthroughContext(), PassthroughContext(), PassthroughContext(), PassthroughContext(), False)
        ptw_name = result[0]['cores'][0]['PTW']
        ptws = result[0]['ptws']

        self.assertIn(ptw_name, [c['name'] for c in ptws])

    def test_instruction_caches_have_instruction_prefetchers(self):
        for num_cores in (1,2,4,8):
            with self.subTest(num_cores=num_cores):
                config_cores = [{ 'name': 'test_cpu'+str(i) } for i in range(num_cores)]

                result = config.parse.parse_normalized(config_cores, {}, {}, {}, {}, {}, PassthroughContext(), PassthroughContext(), PassthroughContext(), PassthroughContext(), False)
                cache_names = [core['L1I'] for core in result[0]['cores']]
                caches = result[0]['caches']

                instruction_caches = [caches[[cache['name'] for cache in caches].index(name)] for name in cache_names]
                is_inst_data = {c['name']:[d['_is_instruction_prefetcher'] for d in c['_prefetcher_data']] for c in caches if c['name'] in cache_names}
                self.assertEqual(is_inst_data, {n:[True] for n in cache_names})

    def test_instruction_and_data_caches_have_translators(self):
        for num_cores in (1,2,4,8):
            with self.subTest(num_cores=num_cores):
                config_cores = [{ 'name': 'test_cpu'+str(i) } for i in range(num_cores)]

                result = config.parse.parse_normalized(config_cores, {}, {}, {}, {}, {}, PassthroughContext(), PassthroughContext(), PassthroughContext(), PassthroughContext(), False)
                cache_names = [core['L1I'] for core in result[0]['cores']] + [core['L1D'] for core in result[0]['cores']]
                caches = result[0]['caches']

                filtered_caches = [caches[[cache['name'] for cache in caches].index(name)] for name in cache_names]
                tlb_names = {c['name']: ('lower_translate' in c) for c in filtered_caches}

                self.assertEqual(tlb_names, {c:True for c in tlb_names.keys()})

    def test_the_end_of_the_data_path_is_dram(self):
        for num_cores, name in itertools.product((1,2,4,8), ('L1I', 'L1D')):
            with self.subTest(ptw=name, num_cores=num_cores):
                config_cores = [{ 'name': 'test_cpu'+str(i) } for i in range(num_cores)]

                result = config.parse.parse_normalized(config_cores, {}, {}, {}, {}, {}, PassthroughContext(), PassthroughContext(), PassthroughContext(), PassthroughContext(), False)
                cache_names = [c['name'] for c in result[0]['caches']]
                ll_names = [c.get('lower_level') for c in result[0]['caches']]

                for cpu in result[0]['cores']:
                    active_name = cpu[name]
                    path = [active_name]
                    while active_name in cache_names:
                        active_name = ll_names[cache_names.index(active_name)]
                        path.append(active_name)

                    self.assertEqual(path[-1], 'DRAM')

    def test_the_end_of_the_tlb_path_is_a_ptw(self):
        for num_cores, name in itertools.product((1,2,4,8), ('ITLB', 'DTLB')):
            with self.subTest(ptw=name, num_cores=num_cores):
                config_cores = [{ 'name': 'test_cpu'+str(i) } for i in range(num_cores)]

                result = config.parse.parse_normalized(config_cores, {}, {}, {}, {}, {}, PassthroughContext(), PassthroughContext(), PassthroughContext(), PassthroughContext(), False)
                cache_names = [c['name'] for c in result[0]['caches']]
                ptw_names = [c['name'] for c in result[0]['ptws']]
                ll_names = [c.get('lower_level') for c in result[0]['caches']]

                for cpu in result[0]['cores']:
                    active_name = cpu[name]
                    path = [active_name]
                    while active_name in cache_names:
                        active_name = ll_names[cache_names.index(active_name)]
                        path.append(active_name)

                    self.assertIn(path[-1], ptw_names)

    def test_tlbs_do_not_need_translation(self):
        for num_cores in (1,2,4,8):
            with self.subTest(num_cores=num_cores):
                config_cores = [{ 'name': 'test_cpu'+str(i) } for i in range(num_cores)]

                result = config.parse.parse_normalized(config_cores, {}, {}, {}, {}, {}, PassthroughContext(), PassthroughContext(), PassthroughContext(), PassthroughContext(), False)
                cache_names = [core['ITLB'] for core in result[0]['cores']] + [core['DTLB'] for core in result[0]['cores']]
                caches = result[0]['caches']

                filtered_caches = [caches[[cache['name'] for cache in caches].index(name)] for name in cache_names]
                tlb_names = {c['name']: ('lower_translate' in c) for c in filtered_caches}

                self.assertEqual(tlb_names, {c:False for c in tlb_names.keys()})

    def test_caches_inherit_core_frequency(self):
        for num_cores in (1,2,4,8):
            with self.subTest(num_cores=num_cores):
                config_cores = [{ 'name': 'test_cpu'+str(i), 'frequency': random.randrange(20162016) } for i in range(num_cores)]

                result = config.parse.parse_normalized(config_cores, {}, {}, {}, {}, {}, PassthroughContext(), PassthroughContext(), PassthroughContext(), PassthroughContext(), False)
                for name in ('L1I', 'L1D', 'ITLB', 'DTLB'):
                    cache_names_and_frequencies = [(core[name], core['frequency']) for core in result[0]['cores']]
                    caches = result[0]['caches']

                    for cache_name, frequency in cache_names_and_frequencies:
                        cache_freq = caches[[cache['name'] for cache in caches].index(cache_name)].get('frequency')
                        self.assertEqual(frequency, cache_freq)

    def test_cores_have_branch_predictors_and_btbs(self):
        for num_cores, module_key in itertools.product((1,2,4,8), ('_branch_predictor_data', '_btb_data')):
            with self.subTest(num_cores=num_cores, module_key=module_key):
                config_cores = [{ 'name': 'test_cpu'+str(i) } for i in range(num_cores)]

                result = config.parse.parse_normalized(config_cores, {}, {}, {}, {}, {}, PassthroughContext(), PassthroughContext(), PassthroughContext(), PassthroughContext(), False)
                cores = result[0]['cores']

                module_names = [c.get(module_key) for c in cores]
                self.assertNotIn(None, module_names)

    def test_caches_have_prefetchers_and_replacement(self):
        for num_cores, module_key in itertools.product((1,2,4,8), ('_prefetcher_data', '_replacement_data')):
            with self.subTest(num_cores=num_cores, module_key=module_key):
                config_cores = [{ 'name': 'test_cpu'+str(i) } for i in range(num_cores)]

                result = config.parse.parse_normalized(config_cores, {}, {}, {}, {}, {}, PassthroughContext(), PassthroughContext(), PassthroughContext(), PassthroughContext(), False)
                caches = result[0]['caches']

                module_names = [c.get(module_key) for c in caches]
                self.assertNotIn(None, module_names)

class NormalizeConfigTest(unittest.TestCase):

    def test_empty_config_creates_defaults(self):
        cores, caches, ptws, pmem, vmem, root = config.parse.normalize_config({})
        self.assertEqual(len(cores), 1)
        self.assertEqual(caches, {})
        self.assertEqual(ptws, {})
        self.assertEqual(pmem, {})
        self.assertEqual(vmem, {})

    def test_caches_in_root_are_moved_to_cache_array(self):
        for name in ('L1I', 'L1D', 'ITLB', 'DTLB', 'L2C', 'STLB'):
            with self.subTest(cache_name=name):
                test_config = {
                        name: {
                            'name': 'testcache',
                            '__test__': True
                        }
                    }
                cores, caches, ptws, pmem, vmem, root = config.parse.normalize_config(test_config)
                self.assertIn('testcache', caches)
                self.assertEqual(caches['testcache'].get('__test__'), True)

    def test_ptws_in_cores_are_moved_to_cache_array(self):
        test_config = {
                'PTW': {
                    '__test__': True
                }
            }
        cores, caches, ptws, pmem, vmem, root = config.parse.normalize_config(test_config)
        self.assertIn(cores[0]['PTW'], ptws)
        self.assertEqual(ptws[cores[0]['PTW']].get('__test__'), True)

    def test_caches_in_cores_are_moved_to_cache_array(self):
        for name in ('L1I', 'L1D', 'ITLB', 'DTLB', 'L2C', 'STLB'):
            with self.subTest(cache_name=name):
                test_config = {
                        'ooo_cpu': [{name: {
                            '__test__': True
                        }}]
                    }
                cores, caches, ptws, pmem, vmem, root = config.parse.normalize_config(test_config)
                self.assertIn(cores[0][name], caches)
                self.assertEqual(caches[cores[0][name]].get('__test__'), True)

    def test_ptws_in_cores_are_moved_to_cache_array(self):
        test_config = {
                'ooo_cpu': [{'PTW': {
                    '__test__': True
                }}]
            }
        cores, caches, ptws, pmem, vmem, root = config.parse.normalize_config(test_config)
        self.assertIn(cores[0]['PTW'], ptws)
        self.assertEqual(ptws[cores[0]['PTW']].get('__test__'), True)

    def test_cache_array_is_forwarded(self):
        test_config = {
                'caches': [{
                    'name': 'testcache',
                    '__test__': True
                }]
            }
        cores, caches, ptws, pmem, vmem, root = config.parse.normalize_config(test_config)
        self.assertIn('testcache', caches)
        self.assertEqual(caches['testcache'].get('__test__'), True)

    def test_ptw_array_is_forwarded(self):
        test_config = {
                'ptws': [{
                    'name': 'testcache',
                    '__test__': True
                }]
            }
        cores, caches, ptws, pmem, vmem, root = config.parse.normalize_config(test_config)
        self.assertIn('testcache', ptws)
        self.assertEqual(ptws['testcache'].get('__test__'), True)

    def test_physical_memory_is_forwarded(self):
        test_config = {
                'physical_memory': {
                    '__test__': True
                }
            }
        cores, caches, ptws, pmem, vmem, root = config.parse.normalize_config(test_config)
        self.assertEqual(pmem.get('__test__'), True)

    def test_virtual_memory_is_forwarded(self):
        test_config = {
                'virtual_memory': {
                    '__test__': True
                }
            }
        cores, caches, ptws, pmem, vmem, root = config.parse.normalize_config(test_config)
        self.assertEqual(vmem.get('__test__'), True)

    def test_core_params_are_moved_to_core_array(self):
        core_keys_to_copy = ('frequency', 'ifetch_buffer_size', 'decode_buffer_size', 'dispatch_buffer_size', 'rob_size', 'lq_size', 'sq_size', 'fetch_width', 'decode_width', 'dispatch_width', 'execute_width', 'lq_width', 'sq_width', 'retire_width', 'mispredict_penalty', 'scheduler_size', 'decode_latency', 'dispatch_latency', 'schedule_latency', 'execute_latency', 'branch_predictor', 'btb', 'DIB')
        for k in core_keys_to_copy:
            with self.subTest(key=k):
                cores, caches, ptws, pmem, vmem, root = config.parse.normalize_config({ k: '__test__' })
                self.assertEqual(cores[0].get(k), '__test__')

    def test_core_array_params_are_preferred(self):
        test_config = {
            'ooo_cpu': [ { 'rob_size': 2016 } ],
            'rob_size': 1028
        }
        cores, caches, ptws, pmem, vmem, root = config.parse.normalize_config(test_config)
        self.assertEqual(cores[0].get('rob_size'), 2016)

    def test_core_array_params_are_preferred_multi(self):
        test_config = {
            'num_cores': 2,
            'ooo_cpu': [ { 'rob_size': 2016 } ],
            'rob_size': 1028
        }
        cores, caches, ptws, pmem, vmem, root = config.parse.normalize_config(test_config)
        self.assertEqual(cores[0].get('rob_size'), 2016)
        self.assertEqual(cores[1].get('rob_size'), 2016)

    def test_cache_array_params_are_preferred(self):
        test_config = {
            'caches': [ { 'name': 'testcache', '__var__': '__fromarray__' } ],
            'ooo_cpu': [ { 'L1D': { 'name': 'testcache', '__var__': '__fromcore__' } } ],
            'L1D': { 'name': 'testcache', '__var__': '__fromroot__' }
        }
        cores, caches, ptws, pmem, vmem, root = config.parse.normalize_config(test_config)
        self.assertEqual(caches['testcache'].get('__var__'), '__fromarray__')

    def test_cores_in_core_array_can_be_named(self):
        test_config = {
            'ooo_cpu': [ { 'name': 'testcore' } ]
        }
        cores, caches, ptws, pmem, vmem, root = config.parse.normalize_config(test_config)
        self.assertEqual(cores[0].get('name'), 'testcore')

    def test_caches_in_core_array_can_be_named(self):
        test_config = {
            'ooo_cpu': [ { 'L1D': { 'name': 'testcache', '__var__': '__fromcore__' } } ]
        }
        cores, caches, ptws, pmem, vmem, root = config.parse.normalize_config(test_config)
        self.assertIn('testcache', caches)

class MergeConfigurationsTests(unittest.TestCase):
    def test_merging_empty_with_empty_is_empty(self):
        cores, caches, ptws, pmem, vmem, root = config.parse.merge_configs(config.parse.normalize_config({}), config.parse.normalize_config({}))
        self.assertEqual(len(cores), 1)
        self.assertEqual(caches, {})
        self.assertEqual(ptws, {})
        self.assertEqual(pmem, {})
        self.assertEqual(vmem, {})

    def test_merging_empty_with_nonempty_does_not_affect_result(self):
        test_config = {
            'num_cores': 2,
            'ooo_cpu': [ { 'rob_size': 2016 } ],
            'rob_size': 1028
        }
        for configs, label in (((test_config, {}), 'after'), (({}, test_config), 'before')):
            with self.subTest(order=label):
                cores, caches, ptws, pmem, vmem, root = config.parse.merge_configs(*map(config.parse.normalize_config, configs))
                self.assertEqual(cores[0].get('rob_size'), 2016)
                self.assertEqual(cores[1].get('rob_size'), 2016)

    def test_merging_first_takes_priority_in_core_array(self):
        seed_config = config.parse.normalize_config({
            'ooo_cpu': [ { 'rob_size': 2016 } ],
        })
        test_config = config.parse.normalize_config({
            'ooo_cpu': [ { 'rob_size': 2048 } ],
        })
        cores, caches, ptws, pmem, vmem, root = config.parse.merge_configs(seed_config, test_config)
        self.assertEqual(cores[0].get('rob_size'), seed_config[0][0]['rob_size'])

    def test_merging_first_takes_priority_from_root_to_core_array(self):
        seed_config = config.parse.normalize_config({
            'rob_size': 2016
        })
        test_config = config.parse.normalize_config({
            'ooo_cpu': [ { 'rob_size': 2048 } ],
        })
        cores, caches, ptws, pmem, vmem, root = config.parse.merge_configs(seed_config, test_config)
        self.assertEqual(cores[0].get('rob_size'), seed_config[0][0]['rob_size'])

    def test_merging_first_takes_priority_from_core_array_to_root(self):
        seed_config = config.parse.normalize_config({
            'ooo_cpu': [ { 'rob_size': 2048 } ],
        })
        test_config = config.parse.normalize_config({
            'rob_size': 2016
        })
        cores, caches, ptws, pmem, vmem, root = config.parse.merge_configs(seed_config, test_config)
        self.assertEqual(cores[0].get('rob_size'), seed_config[0][0]['rob_size'])

    def test_merging_first_takes_priority_from_cache_array_to_core_array(self):
        seed_config = config.parse.normalize_config({
            'caches': [ { 'name': 'test', 'sets': 2 } ],
            'ooo_cpu': [ { 'L1D': 'test' } ]
        })
        test_config = config.parse.normalize_config({
            'ooo_cpu': [ { 'L1D': { 'name': 'test', 'sets': 3 } } ],
        })
        cores, caches, ptws, pmem, vmem, root = config.parse.merge_configs(seed_config, test_config)
        self.assertEqual(caches, seed_config[1])

class DefaultFrequenciesTest(unittest.TestCase):

    def test_first_level_caches_inherit_core_frequency(self):
        config_cores = [{
            'name': 'test_cpu',
            'frequency': random.randrange(20162016),
            'L1I': 'test_l1i',
            'L1D': 'test_l1d',
            'ITLB': 'test_itlb',
            'DTLB': 'test_dtlb'
        }]

        config_caches = {
            'test_l1i': { 'name': 'test_l1i' },
            'test_l1d': { 'name': 'test_l1d' },
            'test_itlb': { 'name': 'test_itlb' },
            'test_dtlb': { 'name': 'test_dtlb' }
        }

        caches = { c['name']: c for c in config.parse.default_frequencies(config_cores, config_caches) }
        for name in ('L1I', 'L1D', 'ITLB', 'DTLB'):
            self.assertEqual(config_cores[0]['frequency'], caches[config_cores[0][name]].get('frequency'))

    def test_frequencies_propogate_downward(self):
        config_cores = [{
            'name': 'test_cpu',
            'frequency': random.randrange(20162016),
            'L1I': 'test_l1i',
            'L1D': 'test_l1d',
            'ITLB': 'test_itlb',
            'DTLB': 'test_dtlb'
        }]

        config_caches = {
            'test_l1i': { 'name': 'test_l1i', 'lower_level': 'test_l2c' },
            'test_l1d': { 'name': 'test_l1d', 'lower_level': 'test_l2c' },
            'test_itlb': { 'name': 'test_itlb', 'lower_level': 'test_stlb' },
            'test_dtlb': { 'name': 'test_dtlb', 'lower_level': 'test_stlb' },
            'test_l2c': { 'name': 'test_l2c' },
            'test_stlb': { 'name': 'test_stlb' }
        }

        caches = { c['name']: c for c in config.parse.default_frequencies(config_cores, config_caches) }
        for name in ('test_l2c', 'test_stlb'):
            self.assertEqual(config_cores[0]['frequency'], caches[name].get('frequency'))

    def test_frequencies_are_not_overwritten(self):
        config_cores = [{
            'name': 'test_cpu',
            'frequency': random.randrange(20162016),
            'L1I': 'test_l1i',
            'L1D': 'test_l1d',
            'ITLB': 'test_itlb',
            'DTLB': 'test_dtlb'
        }]

        config_caches = {
            'test_l1i': { 'name': 'test_l1i', 'lower_level': 'test_l2c' },
            'test_l1d': { 'name': 'test_l1d', 'lower_level': 'test_l2c' },
            'test_itlb': { 'name': 'test_itlb', 'lower_level': 'test_stlb' },
            'test_dtlb': { 'name': 'test_dtlb', 'lower_level': 'test_stlb' },
            'test_l2c': { 'name': 'test_l2c', 'frequency': 55555555 },
            'test_stlb': { 'name': 'test_stlb', 'frequency': 66666666 }
        }

        caches = { c['name']: c for c in config.parse.default_frequencies(config_cores, config_caches) }
        for name in ('test_l2c', 'test_stlb'):
            self.assertEqual(config_caches[name]['frequency'], caches[name].get('frequency'))

    def test_frequencies_take_the_maximum_of_upper_levels(self):
        config_cores = [{
            'name': 'test_cpu',
            'frequency': 1,
            'L1I': 'test_l1i',
            'L1D': 'test_l1d',
            'ITLB': 'test_itlb',
            'DTLB': 'test_dtlb'
        }]

        config_caches = {
            'test_l1i': { 'name': 'test_l1i', 'lower_level': 'test_l2c', 'frequency': 2 },
            'test_l1d': { 'name': 'test_l1d', 'lower_level': 'test_l2c', 'frequency': 3 },
            'test_itlb': { 'name': 'test_itlb' },
            'test_dtlb': { 'name': 'test_dtlb' },
            'test_l2c': { 'name': 'test_l2c' }
        }

        caches = { c['name']: c for c in config.parse.default_frequencies(config_cores, config_caches) }
        self.assertEqual(caches['test_l2c'].get('frequency'), 3)

class CoreDefaultNamesTests(unittest.TestCase):

    def test_core_with_only_name_gets_default_names(self):
        testval = {'name': 'testcpu'}
        result = config.parse.core_default_names(testval)
        self.assertEqual(result.get('name'), testval.get('name'))
        self.assertIn('L1I', result)
        self.assertIn('L1D', result)
        self.assertIn('ITLB', result)
        self.assertIn('DTLB', result)
        self.assertIn('PTW', result)
        self.assertIn('frequency', result)
        self.assertIn('DIB', result)

    def test_given_names_are_not_overwritten(self):
        for name in ('L1I', 'L1D', 'ITLB', 'DTLB', 'PTW', 'branch_predictor', 'btb', 'frequency', 'DIB'):
            with self.subTest(name=name):
                testval = {'name': 'testcpu', name: 'testname'}
                result = config.parse.core_default_names(testval)
                self.assertEqual(result.get(name), testval.get(name))

class EnvironmentParseTests(unittest.TestCase):

    def setUp(self):
        self.base_config = (
            [{
                'name': 'test_cpu'
            }],
            {
            },
            {
            },
            {},
            {}
        )

    def test_cc_passes_through(self):
        test_config = { 'CC': 'cc' }
        result = config.parse.parse_normalized(*self.base_config, test_config, PassthroughContext(), PassthroughContext(), PassthroughContext(), PassthroughContext(), False)
        self.assertEqual(test_config, result[4])

    def test_cxx_passes_through(self):
        test_config = { 'CXX': 'cxx' }
        result = config.parse.parse_normalized(*self.base_config, test_config, PassthroughContext(), PassthroughContext(), PassthroughContext(), PassthroughContext(), False)
        self.assertEqual(test_config, result[4])

    def test_cppflags_passes_through(self):
        test_config = { 'CPPFLAGS': 'cppflags' }
        result = config.parse.parse_normalized(*self.base_config, test_config, PassthroughContext(), PassthroughContext(), PassthroughContext(), PassthroughContext(), False)
        self.assertEqual(test_config, result[4])

    def test_cxxflags_passes_through(self):
        test_config = { 'CXXFLAGS': 'cxxflags' }
        result = config.parse.parse_normalized(*self.base_config, test_config, PassthroughContext(), PassthroughContext(), PassthroughContext(), PassthroughContext(), False)
        self.assertEqual(test_config, result[4])

    def test_ldflags_passes_through(self):
        test_config = { 'LDFLAGS': 'ldflags' }
        result = config.parse.parse_normalized(*self.base_config, test_config, PassthroughContext(), PassthroughContext(), PassthroughContext(), PassthroughContext(), False)
        self.assertEqual(test_config, result[4])

    def test_ldlibs_passes_through(self):
        test_config = { 'LDLIBS': 'ldlibs' }
        result = config.parse.parse_normalized(*self.base_config, test_config, PassthroughContext(), PassthroughContext(), PassthroughContext(), PassthroughContext(), False)
        self.assertEqual(test_config, result[4])

class ConfigRootPassthroughParseTests(unittest.TestCase):

    def setUp(self):
        self.base_config = (
            [{
                'name': 'test_cpu'
            }],
            {
            },
            {
            },
            {},
            {}
        )

    def test_block_size_passes_through(self):
        test_config = { 'block_size': 27 }
        result = config.parse.parse_normalized(*self.base_config, test_config, PassthroughContext(), PassthroughContext(), PassthroughContext(), PassthroughContext(), False)
        self.assertIn('block_size', result[3])
        self.assertEqual(test_config.get('block_size'), result[3].get('block_size'))

    def test_page_size_passes_through(self):
        test_config = { 'page_size': 27 }
        result = config.parse.parse_normalized(*self.base_config, test_config, PassthroughContext(), PassthroughContext(), PassthroughContext(), PassthroughContext(), False)
        self.assertIn('page_size', result[3])
        self.assertEqual(test_config.get('page_size'), result[3].get('page_size'))

    def test_heartbeat_frequency_passes_through(self):
        test_config = { 'heartbeat_frequency': 27 }
        result = config.parse.parse_normalized(*self.base_config, test_config, PassthroughContext(), PassthroughContext(), PassthroughContext(), PassthroughContext(), False)
        self.assertIn('heartbeat_frequency', result[3])
        self.assertEqual(test_config.get('heartbeat_frequency'), result[3].get('heartbeat_frequency'))

class FoundMoreContext:
    def find(self, module):
        return {'name': module, 'fname': 'xxyzzy/'+module, '_is_instruction_prefetcher': module.endswith('_instr')}

    def find_all(self):
        return [{'name': 'extra', 'fname': 'aaaabbbb/extra', '_is_instruction_prefetcher': False}]

class CompileAllModulesTests(unittest.TestCase):

    def setUp(self):
        self.base_config = (
            [{
                'name': 'test_cpu', 'L1D': 'test_L1D'
            }],
            {
                'test_L1D': { 'name': 'test_L1D' }
            },
            {
            },
            {},
            {}
        )

    def test_no_compile_all_finds_given_branch(self):
        local_config = self.base_config
        local_config[0][0]['branch_predictor'] = 'test_branch'
        result = config.parse.parse_normalized(*local_config, {}, FoundMoreContext(), PassthroughContext(), PassthroughContext(), PassthroughContext(), False)
        self.assertIn('test_branch', result[1])

        result_all = config.parse.parse_normalized(*local_config, {}, FoundMoreContext(), PassthroughContext(), PassthroughContext(), PassthroughContext(), True)
        self.assertIn('test_branch', result_all[1])

    def test_no_compile_all_finds_given_btb(self):
        local_config = self.base_config
        local_config[0][0]['btb'] = 'test_btb'
        result = config.parse.parse_normalized(*local_config, {}, PassthroughContext(), FoundMoreContext(), PassthroughContext(), PassthroughContext(), False)
        self.assertIn('test_btb', result[1])

        result_all = config.parse.parse_normalized(*local_config, {}, PassthroughContext(), FoundMoreContext(), PassthroughContext(), PassthroughContext(), True)
        self.assertIn('test_btb', result_all[1])

    def test_no_compile_all_finds_given_pref(self):
        local_config = self.base_config
        local_config[1]['test_L1D']['prefetcher'] = 'test_pref'
        result = config.parse.parse_normalized(*local_config, {}, PassthroughContext(), PassthroughContext(), FoundMoreContext(), PassthroughContext(), False)
        self.assertIn('test_pref', result[1])

        result_all = config.parse.parse_normalized(*local_config, {}, PassthroughContext(), PassthroughContext(), FoundMoreContext(), PassthroughContext(), True)
        self.assertIn('test_pref', result_all[1])

    def test_no_compile_all_finds_given_repl(self):
        local_config = self.base_config
        local_config[1]['test_L1D']['replacement'] = 'test_repl'
        result = config.parse.parse_normalized(*local_config, {}, PassthroughContext(), PassthroughContext(), PassthroughContext(), FoundMoreContext(), False)
        self.assertIn('test_repl', result[1])

        result_all = config.parse.parse_normalized(*local_config, {}, PassthroughContext(), PassthroughContext(), PassthroughContext(), FoundMoreContext(), True)
        self.assertIn('test_repl', result_all[1])

    def test_compile_all_finds_extra_branch(self):
        result = config.parse.parse_normalized(*self.base_config, {}, FoundMoreContext(), PassthroughContext(), PassthroughContext(), PassthroughContext(), False)
        self.assertNotIn('extra', result[1])

        result_all = config.parse.parse_normalized(*self.base_config, {}, FoundMoreContext(), PassthroughContext(), PassthroughContext(), PassthroughContext(), True)
        self.assertIn('extra', result_all[1])

    def test_compile_all_finds_extra_btb(self):
        result = config.parse.parse_normalized(*self.base_config, {}, PassthroughContext(), FoundMoreContext(), PassthroughContext(), PassthroughContext(), False)
        self.assertNotIn('extra', result[1])

        result_all = config.parse.parse_normalized(*self.base_config, {}, PassthroughContext(), FoundMoreContext(), PassthroughContext(), PassthroughContext(), True)
        self.assertIn('extra', result_all[1])

    def test_compile_all_finds_extra_pref(self):
        result = config.parse.parse_normalized(*self.base_config, {}, PassthroughContext(), PassthroughContext(), FoundMoreContext(), PassthroughContext(), False)
        self.assertNotIn('extra', result[1])

        result_all = config.parse.parse_normalized(*self.base_config, {}, PassthroughContext(), PassthroughContext(), FoundMoreContext(), PassthroughContext(), True)
        self.assertIn('extra', result_all[1])

    def test_compile_all_finds_extra_repl(self):
        result = config.parse.parse_normalized(*self.base_config, {}, PassthroughContext(), PassthroughContext(), PassthroughContext(), FoundMoreContext(), False)
        self.assertNotIn('extra', result[1])

        result_all = config.parse.parse_normalized(*self.base_config, {}, PassthroughContext(), PassthroughContext(), PassthroughContext(), FoundMoreContext(), True)
        self.assertIn('extra', result_all[1])

class PathEndInTests(unittest.TestCase):
    def test_path_end(self):
        for length in (1,2,4,16):
            with self.subTest(length=length):
                path = ({'name': x} for x in range(length))
                result = config.parse.path_end_in(path, 'last')
                self.assertEqual(result, {'name': length-1, 'lower_level': 'last'})
