'''
Created on 2020-05-25

@author: wf
'''
import unittest
from unittest.mock import patch
from wikibot.smw import SMW, SMWBot, SMWClient, QueryResultSizeExceedException
from wikibot.wikibot import WikiBot
from wikibot.wikiclient import WikiClient
from tests.test_wikibot import TestWikiBot
from tests.test_WikiUser import TestWikiUser
from datetime import datetime

class TestSMW(unittest.TestCase):
    """ test access to SemanticMediaWiki API see https://www.semantic-mediawiki.org/wiki/Help:API:ask"""

    # sample queries
    testask1="""{{#ask:  [[Concept:Semantic MediaWiki Cons 2012]]
        |?Has_Wikidata_item_ID = WikiDataId
        |?Has planned finish = finish
        |?Has planned start =    start
        |?Has_location  =        location
        |  format=table  }}"""
        
    def setUp(self):
        '''
        general setup
        '''
        self.debug=False
        pass


    def tearDown(self):
        '''
        general tear down
        '''
        pass

    
    def testFixAsk(self):
        """ test fixing an ask query to be made fit for API use"""
        smw=SMW()
        fixedAsk=smw.fixAsk(TestSMW.testask1)
        expected="""[[Concept:Semantic_MediaWiki_Cons_2012]]|?Has_Wikidata_item_ID=WikiDataId|?Has_planned_finish=finish|?Has_planned_start=start|?Has_location=location|format=table"""
        if self.debug:
            print(fixedAsk)
        self.assertEqual(expected,fixedAsk)
        
    def testGetConcept(self):
        """ test extracting a concept from an ask query"""
        smw=SMW()
        fixedAsk=smw.fixAsk(TestSMW.testask1)
        concept=smw.getConcept(fixedAsk)
        if self.debug:
            print(concept)
        self.assertEqual(concept,"Semantic_MediaWiki_Cons_2012")
        
    def getSMWs(self,wikiId='smwcopy'):
        ''' get the alternative SMW access instances for the given wiki id
        '''
        wikiuser=TestWikiUser.getSMW_WikiUser(wikiId)
        wikibot=WikiBot.ofWikiUser(wikiuser)
        wikiclient=WikiClient.ofWikiUser(wikiuser)
        smwbot=SMWBot(wikibot.site)
        smwclient=SMWClient(wikiclient.getSite())
        return [smwbot,smwclient]
         
    def testGetEvents(self):
        ''' text for issue #6 https://github.com/WolfgangFahl/py-3rdparty-mediawiki/issues/6 '''    
        limit=20
        ask="""{{#ask: [[Acronym::+]][[Ordinal::>5]]
    |mainlabel=Event
    | ?Acronym = acronym
    | ?Has location city = city
    | ?Ordinal=ordinal
    | ?_CDAT=creation date
    | ?_MDAT=modification date
    | limit=%d
    |format=table
    }}
    """ % limit
        #self.debug=True
        for smw in self.getSMWs("or"):
            result=smw.query(ask,limit=limit)
            if self.debug:
                print (len(result))
                print (result)  
            self.assertEqual(limit,len(result))    
            fields=['Event','acronym','city','ordinal','creation_date','modification_date']
            for record in result.values():
                for field in fields:
                    self.assertTrue(field in record)
            
    def testSMWInfo(self):
        """ test the SMW Info call"""
        for smw in self.getSMWs():
            result=smw.info()
            if (self.debug):
                print (result)
            self.assertTrue('info' in result)   
            info=result['info']
            expectedlist=['propcount','usedpropcount','declaredpropcount']
            for expected in expectedlist:
                self.assertTrue(expected in info)
                
    def testSMWAskRaw(self):
        """ test getting the raw result of an ask query"""
        for smw in self.getSMWs():
            result=smw.rawquery(TestSMW.testask1)
            if self.debug:
                print (result)
            self.assertTrue('query' in result)
            query=result['query']
            self.assertTrue('printrequests' in query)
            self.assertTrue('results' in query)
        
    # Helpers for parsing the result of isoformat()
    # https://github.com/python/cpython/blob/master/Lib/datetime.py
    def dateFromIso(self,dtstr):
        # It is assumed that this function will only be called with a
        # string of length exactly 10, and (though this is not used) ASCII-only
        year = int(dtstr[0:4])
        if dtstr[4] != '-':
            raise ValueError('Invalid date separator: %s' % dtstr[4])
    
        month = int(dtstr[5:7])
    
        if dtstr[7] != '-':
            raise ValueError('Invalid date separator')
    
        day = int(dtstr[8:10])
    
        return datetime(year, month, day)
    
    def getAskResult(self,smw,ask,limit=20):
        """ get the query result for the given ask query """
        #PrintRequest.debug=self.debug
        result=smw.query(ask,limit=limit)
        if self.debug:
            print (result)    
        return result;
    
    def checkExpected(self,ask,expectedRecords,debug=False):
        """ check that the given ask query returns the content of the expectedRecords""" 
        for smw in self.getSMWs('smwcopy'):
            result=self.getAskResult(smw,ask)
            if debug:
                print(result)
            self.assertEqual(len(expectedRecords),len(result))
            resultlist=list(result.items())
            for i in range(len(expectedRecords)):
                expectedRecord=expectedRecords[i]
                recordkey,record=resultlist[i];
                for key in expectedRecord.keys():
                    self.assertEqual(expectedRecord[key],record[key]) 
        
    def testSMWAsk(self):
        """ test getting the unserialized json result of an ask query"""
        expectedRecords=[{
            'WikiDataId': 'Q42407116', 
            'location':'Cologne, Germany',
            'start':self.dateFromIso('2012-10-24'),
            'finish':self.dateFromIso('2012-10-26')
            },{
            'WikiDataId': 'Q42407127', 
            'location':'Carlsbad, CA, USA',
            'start':self.dateFromIso('2012-04-25'),
            'finish':self.dateFromIso('2012-04-27')
            }]
        self.checkExpected(TestSMW.testask1,expectedRecords)   
        
    # test the SMWBaseURL    
    def testSMWBaseUrl(self):
        wikibot=TestWikiBot.getSMW_Wiki()
        if TestSMW.debug:
            print(wikibot.scriptPath)
        self.assertEqual("/w",wikibot.scriptPath)
        
    # issue https://github.com/WolfgangFahl/py-3rdparty-mediawiki/issues/3
    # see https://www.semantic-mediawiki.org/wiki/User:WolfgangFahl/Workdocumentation_2020-06-01
    def testSMWAskwWithEmptyLink(self):
        ask="""
        {{#ask: [[Category:Event]]
|mainlabel=Event
|?Has_local_chair=chair
|format=table
}}
        """
        for smw in self.getSMWs('or'):
            result=self.getAskResult(smw,ask)
            self.assertTrue(len(result)>7)
                
    def testSMWAskWithMainLabel(self):
        ask="""{{#ask:
 [[Category:City]]
 [[Located in::Germany]] 
 |mainlabel=City
 |?Population 
 |?Area#km² = Size in km²
}}"""
        expectedRecords=[{
            'City':'Demo:Berlin',
            'Population': 3520061, 
            },{
            'City':'Demo:Cologne',
            'Population': 1080394, 
            },{
            'City':'Demo:Frankfurt',    
            'Population': 679664, 
            },{
            'City':'Demo:Munich',    
            'Population': 1353186, 
            },{
            'City':'Demo:Stuttgart',    
            'Population': 606588, 
            },{
            'City':'Demo:Würzburg',   
            'Population': 126635, 
            }]
        self.checkExpected(ask, expectedRecords)   
        
    def testIssue5(self):
        '''
        https://github.com/WolfgangFahl/py-3rdparty-mediawiki/issues/5
        Support more datatypes
        '''
        # https://www.semantic-mediawiki.org/wiki/Help:List_of_datatypes
        properties=[
            "Has annotation uri",
            "Has boolean",
            "Has code",
            "Has date",
            "Has SMW issue ID",
            "Has email address",
            "Has coordinates",
            "Has keyword",
            "Has number",
            "Has mlt",
            "Has example",
            "Has area",
            "Has Wikidata reference",
            "Has conservation status",
            "Telephone number",
            "Has temperatureExample",
            "SomeProperty",
            "Has URL"            
        ]
        #PrintRequest.debug=True
        for prop in properties:
            ask="""{{#ask:[[%s::+]]
 |?%s
 |format=json
 |limit=1
}}
""" % (prop,prop)
            for smw in self.getSMWs('smwcopy'):
                result=self.getAskResult(smw,ask)
                debug=True
                if debug:
                    print("%s: %s" % (prop,result))
                self.assertTrue(len(result)>=1)
                record=list(result.values())[0]
                #print(record.keys())
                self.assertTrue(prop in record.keys())

    def testArgumentValueExtraction(self):
        """ test if the argument value is correctly extracted from a given query"""
        # Test extraction
        expected=12
        self.assertEqual(SMW.getOuterMostArgumentValueOfQuery("limit", "[[Category:Person]]|limit=12"),expected,
                         "Unable to extract the argument")
        self.assertEqual(SMW.getOuterMostArgumentValueOfQuery("limit", "[[Category:Person]]|LIMIT=12"), expected,
                         "Unable to extract the argument written as 'LIMIT' (Extraction should not be case sensitive)")
        self.assertEqual(SMW.getOuterMostArgumentValueOfQuery("limit", "[[Category:Person]]|LiMiT=12"), expected,
                         "Unable to extract the argument written as 'LiMiT' (Extraction should not be case sensitive)")
        self.assertEqual(SMW.getOuterMostArgumentValueOfQuery("limit", "[[Category:Person]] | limit = 12"), expected,
                         "Unable to extract the argument")
        self.assertEqual(SMW.getOuterMostArgumentValueOfQuery("limit", "[[Category:Person]]|  limit=  12"), expected,
                         "Unable to extract the argument")
        self.assertEqual(SMW.getOuterMostArgumentValueOfQuery("limit", "[[Category:Person]]|limit   =12"), expected,
                         "Unable to extract the argument")
        self.assertEqual(SMW.getOuterMostArgumentValueOfQuery("arg", "[[arg = 1]]|arg=12"), expected,
                         "Incorrect extraction of arg")
        expected=7
        self.assertEqual(SMW.getOuterMostArgumentValueOfQuery("arg", "[[Category:Person]]|offset=12 | arg=7 | limit=5"),
                         expected, "Unable to detect arg if other arguments are present")
        self.assertEqual(SMW.getOuterMostArgumentValueOfQuery("arg", "[[Category:Person]]|arg=12 | arg=7 | limit=5"),
                         expected, "Unable to detect last occurring argument arg correctly")
        # Test handling of invalid input
        self.assertEqual(SMW.getOuterMostArgumentValueOfQuery("arg", "[[Category:Person]]"), None,
                         "Incorrect response to query without the argument. None should be returned")
        self.assertEqual(SMW.getOuterMostArgumentValueOfQuery(None, "[[Category:Person]]"), None,
                         "Incorrect response to None as argument. None should be returned")
        self.assertEqual(SMW.getOuterMostArgumentValueOfQuery("", "[[Category:Person]]"), None,
                         "Incorrect response to argument being an empty string. None should be returned")
        self.assertEqual(SMW.getOuterMostArgumentValueOfQuery("args", "[[args=1]]"), None,
                         "Argument should not be detected inside the page selection condition.")
        self.assertEqual(SMW.getOuterMostArgumentValueOfQuery("arg", ""), None, "Incorrect response for empty query")
        self.assertEqual(SMW.getOuterMostArgumentValueOfQuery("arg", None), None,
                         "Missing error handling for None as query input")
        # Test if decimal numbers as value lead to None (Only integers should be extracted)
        self.assertEqual(SMW.getOuterMostArgumentValueOfQuery("arg", "[[Category:Person]]|arg=12.5"), None,
                         "Decimal number was extracted as correct value. Only integers should be extracted.")
 

    def testQueryDivision(self):
        """
        Tests if the queries are correctly divided into equidistant subintervals.
        Checks if the query is divided correctly by returning returning specific results for each expected query
        and comparing it to finally returned unified results.
        """
        DIVISION_STEPS = 10
        QUERY = "[[Modification date::+]]"
        RESULT_N = lambda n: {"query-continue-offset": 1,
                              "query": {
                                  "printrequests": [{}],
                                  "results": {"id": 10**(n-1)},
                                  "serializer": "SMW\\Serializers\\QueryResultSerializer",
                                  "version": 2,
                                  "meta": {
                                      "hash": "7dac6c9084397e1a6a35db7a323c7259",
                                      "count": 1,
                                      "offset": 0,
                                      "source": "",
                                      "time": "0.001692"}
                              }}

        def _askForAllResults_mock_sideEffect(query,limit):
            for i in range(1, DIVISION_STEPS+1):
                day = lambda n: n if n>=10 else f"0{n}"
                expectedQuery = QUERY+ f"|[[Modification date:: >=2020-01-{day(i)}T00:00:00]]|[[Modification date:: " \
                                       f"<=2020-01-{day(i+1)}T00:00:00]]"
                if query == expectedQuery:
                    return [RESULT_N(i)]

        with patch("wikibot.smw.SMWClient.askForAllResults") as askForAllResults_mock, \
                patch("wikibot.smw.SMWClient.getBoundariesOfQuery") as getBoundariesOfQuery:
            getBoundariesOfQuery.return_value = (datetime.strptime("01/01/2020 00:00:00", '%d/%m/%Y %H:%M:%S'),
                                                 datetime.strptime("11/01/2020 00:00:00", '%d/%m/%Y %H:%M:%S'))
            askForAllResults_mock.side_effect = _askForAllResults_mock_sideEffect
            for smw in self.getSMWs():
                if isinstance(smw, SMWClient):
                    smw.queryDivision = DIVISION_STEPS
                    results = smw.askPartitionQuery(QUERY)
                    match = 0
                    for res in results:
                        id = res.get("query").get("results").get("id")
                        match += id
                    self.assertEqual(str(match), "1"*DIVISION_STEPS)

    def testContinuousResultExtraction(self):
        """
        Tests if the large results that exceed either the $smwgQUpperbound or $smwgQDefaultLimit result in the
        QueryResultSizeExceedException Exception.
        Furthermore, it is tested if large results that are below the wiki limit are all queried over the
        continue-offset indication for more results and if the querying stops if the continue-offset attribute is not
        set.
        """
        QUERY = "[[Modification date::+]]"
        MAX  = 100
        RESULTS_PER_RESPONSE = 5   # must correspond to the defined mockup response

        def _raw_api_side_effect_with_oversized_result(action, http_method, *args, **kwargs):
            query = kwargs["query"]
            offset = SMW.getOuterMostArgumentValueOfQuery("offset", query)
            n = int(int(offset)/RESULTS_PER_RESPONSE)+1
            res = self.result_of(n)
            res["query-continue-offset"] = RESULTS_PER_RESPONSE*n if n < MAX/RESULTS_PER_RESPONSE else 0
            return res

        def _raw_api_side_effect_without_oversized_result(action, http_method, *args, **kwargs):
            query = kwargs["query"]
            offset = SMW.getOuterMostArgumentValueOfQuery("offset", query)
            n = int(int(offset)/RESULTS_PER_RESPONSE)+1
            res = self.result_of(n)
            if n < MAX/RESULTS_PER_RESPONSE:
                res["query-continue-offset"] = RESULTS_PER_RESPONSE*n
            return res

        for smw in self.getSMWs():
            if isinstance(smw, SMWClient):
                with patch("mwclient.client.Site.raw_api") as raw_api_mock:
                    # Test if the limit is detected and the partial result returned correctly
                    raw_api_mock.side_effect = _raw_api_side_effect_with_oversized_result
                    self.assertRaises(QueryResultSizeExceedException, smw.askForAllResults, QUERY)
                    with self.assertRaises(QueryResultSizeExceedException) as e:
                        smw.askForAllResults(QUERY)
                    num_res=0
                    for res in e.exception.getResults():
                        r = res.get("query").get("results")
                        num_res += len(r)
                    self.assertEqual(MAX, num_res)
                    # Test handling of normal query (result within the limit)
                    raw_api_mock.side_effect = _raw_api_side_effect_without_oversized_result
                    results = smw.askForAllResults(QUERY)
                    num_res = 0
                    for res in results:
                        r = res.get("query").get("results")
                        num_res += len(r)
                    self.assertEqual(MAX, num_res)

    def testSwitchToQueryDivision(self):
        """
        Test if the query strategy switches to query division if the attribute 'queryDivision' is greater one
        """
        QUERY = "[[Modification date::+]]"
        RESULT = TestSMW.result_of(1)

        def askForAllResults_mock_side_effect(query, limit=None, kwargs={}):
            raise QueryResultSizeExceedException

        for smw in self.getSMWs():
            if isinstance(smw, SMWClient):
                # Test default case
                with patch("wikibot.smw.SMWClient.askForAllResults") as askForAllResults_mock, \
                        patch("wikibot.smw.SMWClient.askPartitionQuery") as askPartitionQuery_mock:
                    askForAllResults_mock.return_value = [RESULT]
                    askPartitionQuery_mock.return_value = None
                    result = smw.ask(QUERY)
                    self.assertEqual(next(result), RESULT)
                    self.assertEqual(askForAllResults_mock.call_count, 1)
                    self.assertEqual(askPartitionQuery_mock.call_count, 0)
                # Test if query division is used if 'queryDivision' attribute is set above 1
                smw.queryDivision = 10
                with patch("wikibot.smw.SMWClient.askForAllResults") as askForAllResults_mock, \
                        patch("wikibot.smw.SMWClient.askPartitionQuery") as askPartitionQuery_mock:
                    askForAllResults_mock.return_value = None
                    askPartitionQuery_mock.return_value = [RESULT]
                    result = smw.ask(QUERY)
                    self.assertEqual(next(result), RESULT)
                    self.assertEqual(askForAllResults_mock.call_count, 0)
                    self.assertEqual(askPartitionQuery_mock.call_count, 1)

    @staticmethod
    def result_of(n):
        """
        Generates the test results for a potential smw query. The result consists of 5 page results and does not contain
        the continue-offset attribute. The given n indicates the ns result by assigning unique but identifyable ids to
        each page and by setting the offset of the result depending on n.
        Args:
            n(int): Number of the result (MUST be >0)
        Returns:
            Returns a valid smw query result.
        Examples:
            result_of(1) -> First five test pages with the ids (1,2,3,4,5) with offset=0
            result_of(2) -> next five results with the ids (11,22,33,44,55) with offset=5
            result_of(3) -> next five results (111,222,333,444,555) with offset=10
            ...
        """
        return {
                "query": {
                    "printrequests": [
                        {
                            "label": "",
                            "key": "",
                            "redi": "",
                            "typeid": "_wpg",
                            "mode": 2
                        }
                    ],
                    "results": {
                        f"Test {n}": {
                            "id": 1
                        },
                        f"Test {'2' * n}": {
                            "id": {'2' * n}
                        },
                        f"Test {'3' * n}": {
                            "id": {'3' * n}
                        },
                        f"Test {'4' * n}": {
                            "id": {'4' * n}
                        },
                        f"Test {'5' * n}": {
                            "id": {'5' * n}
                        }
                    },
                    "serializer": "SMW\\Serializers\\QueryResultSerializer",
                    "version": 2,
                    "meta": {
                        "hash": "48dd3f31329c3947e407d16f7dd227c3",
                        "count": 5,
                        "offset": 5 * (n - 1) if n > 1 else 0,
                        "source": "",
                        "time": "0.007783"
                    }
                }
            }

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testSMWApi']
    unittest.main()