#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 26 15:40:30 2022

@author: Christos ASKP
"""

import cardano_cli_helper as cli
import helper
from datetime import datetime
import json


# List of addresses you want to send to
RecipientList = [
                    'addr1v86pqugsjsu3enxnxxl9ky8g6eefvddtzvyted4mv0pwuysfj0zhz'
                ] 

# List of stake addresses you want to send to
StakeAddressesOfRecipients = \
    [        
        # 'stake1u9unh8dunl2mj2pwdqm53k7xw4l7p9l2l4egywrdyqwhvnqyd7sx8'
    ]


def main(finRecipientObjList,
        myPaymentAddrFile,
        myPaymentAddrSignKeyFile,
        tokenPolicyID,
        sentTokensLogFile,
        delegatorsLogFile,
        minFee):
    with open(myPaymentAddrFile) as file:
        paymentAddr = file.read()
    with open(delegatorsLogFile, 'r') as jsonlog:
        delegatorsDict = json.load(jsonlog)
    cli.getProtocolJson() # Checks if it already exists, if not gets a new copy

    # Get your payment address TxHashes
    utxos = cli.getAddrUTxOs(paymentAddr) 

    # Get your TxHash which contains the tokens with PolicyID, and your ADA and token amount
    allTxInList = utxos.keys() # Use this as tx_In to consolidate all addresses
    myTxHash = cli.getTxInWithLargestTokenAmount(utxos, tokenPolicyID)
    tokensDict = cli.getTokenListFromTxHash(utxos)
    foreignTokensDict = cli.getForeignTokensFromTokenList(tokensDict, tokenPolicyID)
    if 'ADA' in tokensDict.keys():
        myInitLovelace = tokensDict['ADA']
    else:
        print('Error: no ADA found in address.')
        return False
    if tokenPolicyID in tokensDict.keys():
        myInitToken = tokensDict[tokenPolicyID]
    else:
        print('Error: Could not find token with Policy ID ', tokenPolicyID)
        return False
    print ('myInitLovelace:', myInitLovelace)
    print ('myInitToken:', myInitToken)

    # Send noOfTokens to all your recipients with one Tx
    result = cli.sendTokenToAddr(myPaymentAddrSignKeyFile, allTxInList, myInitLovelace, myInitToken, paymentAddr,
                                 finRecipientObjList, tokenPolicyID, minFee, foreignTokensDict)
    if result == -1:
        print ('Error: Tokens could not be sent.')
        return False

    if cli.waitForTxReceipt(paymentAddr, tokenPolicyID, myTxHash, utxos):
        # Store sent transactions on log file
        now = datetime.now()
        current_time = now.strftime("%Y-%m-%d %H:%M:%S")
        latest_tx = {current_time:{}}
        for recipient in finRecipientObjList:
            latest_tx[current_time][recipient.address] = {}
            latest_tx[current_time][recipient.address]['Stake Addr'] = recipient.stake_address
            latest_tx[current_time][recipient.address]['ADA Received'] = '%.3f'%(recipient.lovelace_amount_received/1000000)
            latest_tx[current_time][recipient.address]['ADA Sent'] = '%.3f'%(recipient.lovelace_amount_to_send/1000000)
            latest_tx[current_time][recipient.address]['Tokens Sent'] = recipient.token_amount_to_send
            # Zero the sum of the total stake for addresses succesfully sent
            try:
                delegatorsDict['sum'][recipient.stake_address] = 0
            except:
                print('Delegator stake address not found.')
        helper.appendLogJson(sentTokensLogFile, latest_tx)
        with open(delegatorsLogFile, 'w') as jsonlog:
            json.dump(delegatorsDict, jsonlog, indent=4, sort_keys=False)
        return True
    else:
        return False


if __name__ == '__main__':
    print('Send one NFT to each delegator in the list.')
    configFile = './config.json'
    myPaymentAddrFile, \
    myPaymentAddrSignKeyFile, \
    tokenPolicyID, \
    sentTokensLogFile, \
    delegatorsLogFile, \
    minFee, \
    finRecipientObjList = helper.parseConfigSendAssets(configFile, StakeAddressesOfRecipients, RecipientList)

    if len(finRecipientObjList) != 0:
        main(finRecipientObjList,
             myPaymentAddrFile,
             myPaymentAddrSignKeyFile,
             tokenPolicyID,
             sentTokensLogFile,
             delegatorsLogFile,
             minFee)
    else:
        print('Empty list of recipients received.')
