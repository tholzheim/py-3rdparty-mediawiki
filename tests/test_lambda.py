'''
Created on 2021-01-23

@author: wf
'''
import unittest

from lodstorage.query import Query

from wikibot.lambda_action import LambdaAction, Code
from wikibot.wikiuser import WikiUser
from wikibot.wikiclient import WikiClient
from wikibot.smw import SMWClient
from wikibot.wikiaction import WikiAction

class TestLambda(unittest.TestCase):
    '''
    test lamdba query/action handling
    '''

    def setUp(self):
        self.debug=False
        self.echoCode = Code("EchoCode", text="""# this is a lambda Action action
# it get's its context from a context dict
rows=context["rows"]
for row in rows:
    print(row)
context["result"]={"message":"%d rows printed" %len(rows)}""",lang="python")
        pass


    def tearDown(self):
        pass

    def getSMW(self,wikiId='orth',url='https://confident.dbis.rwth-aachen.de'):
        smw=None
        wikiclient=None
        wusers=WikiUser.getWikiUsers()
        if 'test' in wusers:
            wuser=wusers[wikiId]
            if wuser.url.startswith(url):
                wikiclient=WikiClient.ofWikiUser(wuser)
                smw=SMWClient(wikiclient.getSite())
        return smw,wikiclient
    
    def testLambda(self):
        '''
        test the lamdba handling
        '''
        smw,wikiclient=self.getSMW()
        if smw is not None:
            wikiAction=WikiAction(smw)
            query= Query("test query",query="[[Capital of::+]]",lang="smw")
            lambdaAction=LambdaAction("test smw query",query=query, code=self.echoCode )
            context={"smw":smw}
            lambdaAction.execute(context=context)
            message=lambdaAction.getMessage(context)
            if self.debug:
                print(message)
            self.assertTrue(message is not None)
            self.assertTrue("printed" in message)
        pass


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()