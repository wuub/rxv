=================
 Yamaha Protocol
=================

The Yamaha receivers with built in networking support a variant of
UPNP control. Their initial function table can be fetched via
http://$IP:80/YamahaRemoteControl/desc.xml. This will describe a set
of all the functions available on the system, as well as their
parameters

**Note:** all XML indentation is for human readability, the protocol
  sends the entire stream as one line with no extra white space.

Control Messages
================

Control messages are sent as POST requests to
http://$IP:80/YamahaRemoteControl/ctrl.

.. highlight:: xml

    <?xml version="1.0" encoding="utf-8"?>
    <YAMAHA_AV cmd="GET">
        <Zone_2>
            <Basic_Status>GetParam</Basic_Status>
        </Zone_2>
    </YAMAHA_AV>


Net Radio
=========

.. highlight:: xml

    <?xml version="1.0" encoding="utf-8" ?>
    <YAMAHA_AV cmd="GET">
        <NET_RADIO>
            <Play_Info>GetParam</Play_Info>
        </NET_RADIO>
    </YAMAHA_AV>


Selecting a station off your bookmarks

.. highlight:: xml

    <YAMAHA_AV cmd="PUT"><Zone_2>
        <Input>
            <Input_Sel>NET RADIO</Input_Sel>
        </Input>
    </Zone_2></YAMAHA_AV>


Then you need to navigate through the menu structure manually with:

.. highlight:: xml

    <YAMAHA_AV cmd="GET">
        <NET_RADIO>
            <List_Info>GetParam</List_Info>
        </NET_RADIO>
    </YAMAHA_AV>


With a response that looks like:

.. highlight:: xml

    <YAMAHA_AV rsp="GET" RC="0"><NET_RADIO><List_Info>
    <Menu_Status>Ready</Menu_Status>
    <Menu_Layer>1</Menu_Layer>
    <Menu_Name>NET RADIO</Menu_Name>
    <Current_List>
        <Line_1><Txt>Bookmarks</Txt><Attribute>Container</Attribute></Line_1>
        <Line_2><Txt>Locations</Txt><Attribute>Container</Attribute></Line_2>
        <Line_3><Txt>Genres</Txt><Attribute>Container</Attribute></Line_3>
        <Line_4><Txt>New Stations</Txt><Attribute>Container</Attribute></Line_4>
        <Line_5><Txt>Popular Stations</Txt><Attribute>Container</Attribute></Line_5>
        <Line_6><Txt>Podcasts</Txt><Attribute>Container</Attribute></Line_6>
        <Line_7><Txt>Help</Txt><Attribute>Container</Attribute></Line_7>
        <Line_8><Txt></Txt><Attribute>Unselectable</Attribute></Line_8>
    </Current_List>
    <Cursor_Position>
        <Current_Line>1</Current_Line>
        <Max_Line>7</Max_Line>
    </Cursor_Position>
    </List_Info></NET_RADIO></YAMAHA_AV>


You then have to send cursor moves manually

.. highlight:: xml

    <YAMAHA_AV cmd="PUT">
        <NET_RADIO>
            <List_Control>
                <Jump_Line>1</Jump_Line>
            </List_Control>
        </NET_RADIO>
    </YAMAHA_AV>


... and select

.. highlight:: xml

    <YAMAHA_AV cmd="PUT">
        <NET_RADIO>
            <List_Control>
                <Direct_Sel>Line_1</Direct_Sel>
            </List_Control>
        </NET_RADIO>
    </YAMAHA_AV>


Also, it's important to not send this until ``Menu_Status`` ==
``Ready``. After a select it might be ``Busy``. If it is, you can't
send any commands, they'll just be ignored.
