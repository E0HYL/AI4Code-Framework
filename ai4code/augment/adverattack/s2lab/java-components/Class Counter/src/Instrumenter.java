
import org.xmlpull.v1.XmlPullParserException;


import soot.*;
import soot.jimple.parser.lexer.LexerException;
import soot.jimple.parser.parser.ParserException;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;
import java.lang.reflect.Array;
import java.util.*;
import java.util.concurrent.ThreadLocalRandom;

import static java.lang.System.exit;




public class Instrumenter {




    public static String slices_path = "";

    private static String dexPath = "";

    private static String apkPath = "";

    private static String outputFolder = "";

    public static String AndroidSdk = "";

    public static String Opaque = "";

    public static String Permission = "";

    public static ArrayList<String> permissions = new ArrayList<String>();

    private static final int THRESHOLD = 100;

    public static  boolean DEBUG = true;



    public static void main(String[] args) {


        if (args.length == 3) {
            apkPath = args[0];
            AndroidSdk = args[1];
            DEBUG = Boolean.parseBoolean(args[2]);
        } else if (args.length == 2){
            apkPath = args[0];
            AndroidSdk = args[1];
        } else {
            System.out.println("Wrong arguments, invocation should be like:\njava -jar calculator.jar <goodware_apk> <Android_sdk_path> ");
            exit(0);
        }
        System.out.println("Configuring the framework..");
        Soot_utlilty config = new Soot_utlilty();
        if (DEBUG) {
            System.out.println("DEBUG : apk at " + apkPath+ "\n\n");
        }

        config.initSoot(apkPath);
        Map<String, ArrayList<String>> goodwares_classes = new HashMap<>();
        ArrayList<SootClass> malwares = new ArrayList<>();
        malwares = config.find_malware_classes();
        System.out.println("Total:"+Integer.toString(malwares.size()));
        return;
        }
    }
