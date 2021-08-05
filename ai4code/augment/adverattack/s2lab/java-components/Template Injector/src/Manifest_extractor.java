import org.w3c.dom.*;
import org.xml.sax.SAXException;
import org.xmlpull.v1.XmlPullParserException;
import pxb.android.axml.AxmlParser;
import pxb.android.axml.AxmlReader;
import soot.Scene;
import soot.SootClass;
import soot.jimple.infoflow.android.axml.*;
import soot.jimple.infoflow.android.manifest.ProcessManifest;

import org.w3c.dom.NodeList;
import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.parsers.ParserConfigurationException;

import java.io.*;
import java.util.*;

public class Manifest_extractor {

    String namespace = "http://schemas.android.com/apk/res/android";
    Soot_utlilty utility = new Soot_utlilty();





    public void addProperties(ArrayList<String> properties, String apkPath,String dir_for_receivers, ArrayList<String> permissions) throws IOException, XmlPullParserException {

        if(Instrumenter.DEBUG){
            System.out.println("DEBUG : Trying to add "+properties+" to Manifest...");
        }
        ProcessManifest processManifest = null;
        processManifest = new ProcessManifest(apkPath);
        Map<String,String> corrispondences = new HashMap<>();
        File relative_names=new File(dir_for_receivers+"/Relative_features.txt");
        if(relative_names.exists()){
            try (BufferedReader br = new BufferedReader(new FileReader(relative_names))) {
                for (String line; (line = br.readLine()) != null; ) {
                    corrispondences.put(line.split(":")[0],line.split(":")[1]);
                }
            } catch (IOException e) {
                e.printStackTrace();
            }
        }
        AXmlHandler axmlh = processManifest.getAXml();
        for (String i : properties){
            String name = i;
            SootClass real_class = Scene.v().getSootClass(name);
            if(corrispondences.containsKey(name)){
                if(Instrumenter.DEBUG){
                    System.out.println("DEBUG : Founf RELATIVE NAME "+name+ " real name to inject "+corrispondences.get(name));
                }
                name=corrispondences.get(name);
                System.out.println(utility.get_if_ancient(real_class,"android.app.Activity"));
            }

            if(utility.get_if_ancient(real_class,"android.app.Activity")) {
                if(Instrumenter.DEBUG){
                    System.out.println("DEBUG : Adding activity "+real_class.getName());
                }
                AXmlNode activity = new AXmlNode("activity", null, axmlh.getDocument().getRootNode());
                activity.addAttribute(new AXmlAttribute<String>("name", name, namespace));
                processManifest.addActivity(activity);
            }else if(utility.get_if_ancient(real_class,"android.content.BroadcastReceiver")) {
                if(Instrumenter.DEBUG){
                    System.out.println("DEBUG : Adding receiver "+real_class.getName());
                }

                File file = new File(dir_for_receivers+"/"+name+".xml");
                if(file.exists()) {
                    DocumentBuilderFactory documentBuilderFactory = DocumentBuilderFactory.newInstance();
                    DocumentBuilder documentBuilder = null;
                    try {
                        documentBuilder = documentBuilderFactory.newDocumentBuilder();
                    } catch (ParserConfigurationException e) {
                        e.printStackTrace();
                    }
                    Document document = null;
                    try {
                        document = documentBuilder.parse(file);
                    } catch (SAXException e) {
                        e.printStackTrace();
                    }
                    document.getDocumentElement().normalize();
                    NodeList nodeList = document.getElementsByTagName("receiver");
                    for (int index = 0; index < nodeList.getLength(); index++) {
                        AXmlNode receiver = new AXmlNode("receiver", null, axmlh.getDocument().getRootNode());
                        Node node = nodeList.item(index);
                        NamedNodeMap attributes = node.getAttributes();
                        for (int index_attr = 0; index_attr < attributes.getLength(); index_attr++) {
                            Node attr = attributes.item(index_attr);
                            receiver.addAttribute(new AXmlAttribute<String>(attr.getNodeName(), attr.getNodeValue(), namespace));
                        }
                        NodeList childrens = node.getChildNodes();
                        for (int index_childs = 0; index_childs < childrens.getLength(); index_childs++) {
                            Node child = childrens.item(index_childs);
                            if (child.getNodeName().equals("intent-filter")) {
                                AXmlNode intent_filter = new AXmlNode(child.getNodeName(), null, receiver);
                                NodeList child_attributes = child.getChildNodes();
                                for (int index_child_attr = 0; index_child_attr < child_attributes.getLength(); index_child_attr++) { // childs of intent filters
                                    Node attr = child_attributes.item(index_child_attr);
                                    if (attr.hasAttributes()) {
                                        AXmlNode child_intent = new AXmlNode(attr.getNodeName(), null, intent_filter);
                                        NamedNodeMap childs_of_intents = attr.getAttributes();
                                        for (int index__child_child_attr = 0; index__child_child_attr < childs_of_intents.getLength(); index__child_child_attr++) { //attributes of the childs
                                            Node child_attr = childs_of_intents.item(index__child_child_attr);
                                            child_intent.addAttribute(new AXmlAttribute<String>(child_attr.getNodeName(), child_attr.getNodeValue(), namespace));
                                        }
                                    }
                                }

                            }
                        }
                        processManifest.addReceiver(receiver);

                    }
                }else{
                    AXmlNode service = new AXmlNode("receiver", null, axmlh.getDocument().getRootNode());
                    service.addAttribute(new AXmlAttribute<String>("name", name, namespace));
                    processManifest.addService(service);
                }
            }else if(utility.get_if_ancient(real_class,"android.app.Service")) {
                if(Instrumenter.DEBUG){
                    System.out.println("DEBUG : Adding service "+real_class.getName());
                }
                AXmlNode service = new AXmlNode("service", null, axmlh.getDocument().getRootNode());
                service.addAttribute(new AXmlAttribute<String>("name", name, namespace));
                processManifest.addService(service);
            }else if(utility.get_if_ancient(real_class,"android.content.ContentProvider")) {
                if(Instrumenter.DEBUG){
                    System.out.println("DEBUG : Adding ContentProvider "+real_class.getName());
                }
                AXmlNode provider = new AXmlNode("provider", null, axmlh.getDocument().getRootNode());
                provider.addAttribute(new AXmlAttribute<String>("name", name, namespace));
                processManifest.addProvider(provider);
            }
        }
        if (permissions != null) {
            for (String p : permissions) {
                AXmlNode readLogs = new AXmlNode("uses-permission", null, axmlh.getDocument().getRootNode());
                readLogs.addAttribute(new AXmlAttribute<String>("name", p, this.namespace));
                axmlh.getDocument().getRootNode().addChild(readLogs);
            }
        }
        ArrayList<String> tmp_storage = new ArrayList<>();
        for(Iterator<AXmlNode> iter = processManifest.getAXml().getDocument().getRootNode().getChildren().iterator();iter.hasNext();){
            AXmlNode tmp_node  = iter.next();
            if(!tmp_storage.contains(tmp_node.toString())){
                tmp_storage.add(tmp_node.toString());
            }else{
                processManifest.getAXml().getDocument().getRootNode().removeChild(tmp_node);
            }
        }
        byte[] axmlBA = processManifest.getAXml().toByteArray();
        FileOutputStream fileOuputStream = new FileOutputStream("./AndroidManifest.xml");
        fileOuputStream.write(axmlBA);
        fileOuputStream.close();
        List<File> fileList = new ArrayList<File>();
        File newManifest = new File("./AndroidManifest.xml");
        fileList.add(newManifest);
        ApkHandler apkH = new ApkHandler(apkPath);
        apkH.addFilesToApk(fileList);
    }





}
