
import org.json.JSONArray;
import org.json.JSONException;
import org.xmlpull.v1.XmlPullParserException;


import soot.*;
import soot.jimple.parser.lexer.LexerException;
import soot.jimple.parser.parser.ParserException;

import java.io.*;
import java.lang.reflect.Array;
import java.util.*;
import java.util.concurrent.ThreadLocalRandom;
import org.json.JSONObject;

import static java.lang.System.exit;



public class Instrumenter {




    private static String apkPath = "";


    public static String AndroidSdk = "";

    public static Boolean Export_cc_distribution = false;

    public static String Export_cc_distribution_path = "";



    public static  boolean DEBUG = true;



    public static void main(String[] args) throws JSONException {


        if (args.length == 5) {
            apkPath = args[0];
            AndroidSdk = args[1];
            Export_cc_distribution = Boolean.parseBoolean(args[2]);
            Export_cc_distribution_path = args[3];
            DEBUG = Boolean.parseBoolean(args[4]);
        } else if (args.length == 4){
            apkPath = args[0];
            AndroidSdk = args[1];
            Export_cc_distribution = Boolean.parseBoolean(args[2]);
            Export_cc_distribution_path = args[3];
        } else {
            System.out.println("Wrong arguments, invocation should be like:\njava -jar calculator.jar <malware_apk> <Android_sdk_path> <Export_cc_distribution <true|false>");
            exit(0);
        }
        System.out.println("Configuring the framework..");
        Soot_utlilty config = new Soot_utlilty();
        if (DEBUG) {
            System.out.println("DEBUG : apk at " + apkPath+ "\n\n");
        }

        config.initSoot(apkPath);
        ArrayList<SootClass> malwares = new ArrayList<>();

        malwares = config.find_malware_classes();
        Map<Integer, ArrayList<SootClass>> scores =config.get_scores(malwares);
        if (Export_cc_distribution){
            Map<Integer, ArrayList<SootClass>> to_ret = new HashMap<>();
            Jimple_utility ju = new Jimple_utility();
            JSONArray ja = new JSONArray();
            for(SootClass sc : malwares){
                JSONObject jo = new JSONObject();
                int CC =ju.calculate_cyclomatic_complexity(sc);
                if(!config.isExcludeClassNOASEX(sc)) {
                        jo.put(sc.getName(), CC);
                        ja.put(jo);

                }
            }
            try (FileWriter file = new FileWriter(Export_cc_distribution_path)) {

                file.write(ja.toString());
                file.flush();

            } catch (IOException e) {
                e.printStackTrace();
            }
        }
        Double AVG = config.get_AVG(scores,malwares.size());
        System.out.println("AVG CC:"+AVG);
        return;
        }
    }
