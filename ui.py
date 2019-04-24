# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'chunker.ui'
#
# Created by: PyQt4 UI code generator 4.11.4
#
# WARNING! All changes made in this file will be lost!

from auth import Authorizer
from manager import DownloadManager, UploadManager
from PyQt4 import QtCore, QtGui
from storage import Storage

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8( s ):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate( context, text, disambig ):
        return QtGui.QApplication.translate( context, text, disambig, _encoding )
except AttributeError:
    def _translate( context, text, disambig ):
        return QtGui.QApplication.translate( context, text, disambig )

FILTER_COMBO_BOX_ITEMS = [ 'All files', 'Chunked files' ]
GiB_DIVISOR = 1073741824

class Ui_chunkerMainForm( object ):
    def setupUi( self, chunkerMainForm ):
        chunkerMainForm.setObjectName( _fromUtf8( "chunkerMainForm" ) )
        chunkerMainForm.resize( 803, 545 )
        self.horizontalLayout_2 = QtGui.QHBoxLayout( chunkerMainForm )
        self.horizontalLayout_2.setObjectName( _fromUtf8( "horizontalLayout_2" ) )
        self.horizontalLayout = QtGui.QHBoxLayout(  )
        self.horizontalLayout.setObjectName( _fromUtf8( "horizontalLayout" ) )
        self.accountInfoVerticalLayout = QtGui.QVBoxLayout(  )
        self.accountInfoVerticalLayout.setObjectName( _fromUtf8( "accountInfoVerticalLayout" ) )
        self.summaryHorizontalLayout = QtGui.QHBoxLayout(  )
        self.summaryHorizontalLayout.setObjectName( _fromUtf8( "summaryHorizontalLayout" ) )
        self.sizeSummaryVerticalLayout = QtGui.QVBoxLayout(  )
        self.sizeSummaryVerticalLayout.setObjectName( _fromUtf8( "sizeSummaryVerticalLayout" ) )
        self.totalSizeUsageProgressBar = QtGui.QProgressBar( chunkerMainForm )
        self.totalSizeUsageProgressBar.setProperty( "value", 24 )
        self.totalSizeUsageProgressBar.setObjectName( _fromUtf8( "totalSizeUsageProgressBar" ) )
        self.sizeSummaryVerticalLayout.addWidget( self.totalSizeUsageProgressBar )
        self.totalSizeUsageLabel = QtGui.QLabel( chunkerMainForm )
        self.totalSizeUsageLabel.setText( _fromUtf8( "" ) )
        self.totalSizeUsageLabel.setAlignment( QtCore.Qt.AlignCenter )
        self.totalSizeUsageLabel.setObjectName( _fromUtf8( "totalSizeUsageLabel" ) )
        self.sizeSummaryVerticalLayout.addWidget( self.totalSizeUsageLabel )
        self.summaryHorizontalLayout.addLayout( self.sizeSummaryVerticalLayout )
        self.addUserButton = QtGui.QPushButton( chunkerMainForm )
        self.addUserButton.setObjectName( _fromUtf8( "addUserButton" ) )
        self.summaryHorizontalLayout.addWidget( self.addUserButton )
        self.accountInfoVerticalLayout.addLayout( self.summaryHorizontalLayout )
        self.accountListView = QtGui.QListView( chunkerMainForm )
        self.accountListView.setObjectName( _fromUtf8( "accountListView" ) )
        self.accountInfoVerticalLayout.addWidget( self.accountListView )
        self.horizontalLayout.addLayout( self.accountInfoVerticalLayout )
        self.horizontalLayout_2.addLayout( self.horizontalLayout )
        self.fileVerticalLayout = QtGui.QVBoxLayout(  )
        self.fileVerticalLayout.setObjectName( _fromUtf8( "fileVerticalLayout" ) )
        self.filterHorizontalLayout = QtGui.QHBoxLayout(  )
        self.filterHorizontalLayout.setObjectName( _fromUtf8( "filterHorizontalLayout" ) )
        self.filterLabel = QtGui.QLabel( chunkerMainForm )
        self.filterLabel.setObjectName( _fromUtf8( "filterLabel" ) )
        self.filterHorizontalLayout.addWidget( self.filterLabel )
        self.filterComboBox = QtGui.QComboBox( chunkerMainForm )
        self.filterComboBox.setObjectName( _fromUtf8( "filterComboBox" ) )
        self.filterHorizontalLayout.addWidget( self.filterComboBox )
        self.fileVerticalLayout.addLayout( self.filterHorizontalLayout )
        self.treeView = QtGui.QTreeView( chunkerMainForm )
        self.treeView.setObjectName( _fromUtf8( "treeView" ) )
        self.fileVerticalLayout.addWidget( self.treeView )
        self.horizontalLayout_2.addLayout( self.fileVerticalLayout )

        self.retranslateUi( chunkerMainForm )
        QtCore.QMetaObject.connectSlotsByName( chunkerMainForm )

    def retranslateUi( self, chunkerMainForm ):
        chunkerMainForm.setWindowTitle( _translate( "chunkerMainForm", "Form", None ) )
        self.addUserButton.setText( _translate( "chunkerMainForm", "Add User", None ) )
        self.filterLabel.setText( _translate( "chunkerMainForm", "Show:", None ) )

        auth = Authorizer()
        clients = auth.get_all_clients()
        if len( clients ) > 0:
          total_quota, total_used = 0, 0
          for client in clients:
            quota_gib = float( client.get_quota() ) / GiB_DIVISOR if client.get_quota() else 0
            used_gib = float( client.get_used() ) / GiB_DIVISOR if client.get_used() else 0
            #print( "{0}: {1:1.2f} GB of {2:1.2f} GB used.".format( client.get_username(), used_gib, quota_gib ) )
            total_quota = total_quota + quota_gib
            total_used = total_used + used_gib
          self.filterComboBox.addItems( FILTER_COMBO_BOX_ITEMS )
          self.totalSizeUsageProgressBar.setValue( total_used / total_quota )
          self.totalSizeUsageLabel.setText( "Total Used Space: {0:1.2f} GB of {1:1.2f} GB used.".format( total_used, total_quota ) )
        else:
          self.totalSizeUsageLabel.setText( "You have not linked any accounts to chunker." )
 


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication( sys.argv )
    chunkerMainForm = QtGui.QWidget(  )
    ui = Ui_chunkerMainForm(  )
    ui.setupUi( chunkerMainForm )
    chunkerMainForm.show(  )
    sys.exit( app.exec_(  ) )

