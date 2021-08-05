
import org.xmlpull.v1.XmlPullParserException;


import soot.*;
import soot.jimple.parser.lexer.LexerException;
import soot.jimple.parser.parser.ParserException;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;
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

    private static  int THRESHOLD = 50;

    public static  boolean DEBUG = true;

    private static ArrayList<My_slice> slices_gathered_used = new ArrayList<>();

    private static ArrayList<My_slice> slices_gathered = new ArrayList<>();


    public static void main(String[] args) {


        if (args.length == 9) {
            apkPath = args[0];
            dexPath = args[1];
            outputFolder = args[2];
            AndroidSdk = args[3];
            slices_path = args[4];
            Opaque = args[5];
            Permission = args[6];
            THRESHOLD = Integer.parseInt(args[7]);
            DEBUG = Boolean.parseBoolean(args[8]);
        } else if (args.length == 8){
            apkPath = args[0];
            dexPath = args[1];
            outputFolder = args[2];
            AndroidSdk = args[3];
            slices_path = args[4];
            Opaque = args[5];
            Permission = args[6];
            THRESHOLD = Integer.parseInt(args[7]);
        } else {
            System.out.println("Wrong arguments, invocation should be like:\njava -jar injector.jar <malware_apk> <path_to_jimple_files> <output_folder> <Android_sdk_path> <path_to_mined_slices> <path_to_opaques> <path_to_permissions> <CC Threshold>\nE.g. :java -jar injector.jar /home/jacopo/Documents/feature_extractor/drebin/DroidLyzer/malwares_app/0DE8DEB4FAEF59963EC0EBFDDDBBD9C10D8EBBCE8F23A0B6B0C02BA904E0AA51.apk\n" +
                    "./00ADBDEE7ED68BB4C243F30EA0BABD56C034574303783924DC9654F2916A43E8,/home/jacopo/Documents/work/prism/feature_database/005BE733B7EDD48AC35A42DA985EDC387FB201082FE6891C1D7BF89563D123C7,/home/jacopo/Documents/work/prism/feature_database/070C5B110B0546DDBC42C7E40D145531A693FB764A0D401FBC75E665A30C175E\n" +
                    "./malware_output/\n" +
                    "/root/Android/Sdk/\n" +
                    "./gathered_slices/\n" +
                    "./opaque_preds/sootOutput/Opaque.jimple\n" +
                    "./permissions.txt\n"+
                    "10");
            exit(0);
        }
        System.out.println("Configuring the framework..");
        Soot_utlilty config = new Soot_utlilty();
        if (DEBUG) {
            System.out.println("DEBUG : apk at " + apkPath + ", jimples to inject in " + dexPath + ", slices at " + slices_path + "\n\n");
        }
        String[] folders_input = dexPath.split(",");
        ArrayList<File> directories = new ArrayList<>();
        for (String s : folders_input) {
            if (s.length() > 0) {
                directories.add(new File(s));
            }
        }
        config.initSoot(apkPath, directories, config.get_directories(slices_path), outputFolder);
        Manifest_extractor man_extractor = new Manifest_extractor();
        Map<String, My_slice> slice_corrispondence = new HashMap<>();
        Map<String, ArrayList<String>> goodwares_classes = new HashMap<>();
        ArrayList<SootClass> malwares = new ArrayList<>();
        Map<String, Integer> opaque_scores = config.get_opaque_scores(Opaque);
        permissions = config.extract_permissions(Permission);
        Jimple_utility utility2 = new Jimple_utility();
        if (DEBUG) {
            System.out.println("DEBUG : Load classes to the Scene");
        }
        for (File i : directories) {
            SootClass slice_class = null;
            ArrayList<String> classes = config.get_goodware_classes(i);
            goodwares_classes.put(i.getName(), classes);
            for (String s : classes) {
                if (!s.startsWith("Slice")) {
                    SootClass sc = Scene.v().getSootClass(s);
                    sc.setApplicationClass();
                } else {
                    if (!Scene.v().getSootClass(s).isPhantom()) {
                        File tmp_c = new File(i.getAbsolutePath()+"/"+s+".jimple");
                        if(tmp_c.exists()) {
                            slice_class = Scene.v().getSootClass(s);
                        }
                    }
                }
            }
            System.out.println("Injecting new components into the manifest\n");
            try {
                man_extractor.addProperties(classes, apkPath, i.getAbsolutePath(), permissions);
                Thread.sleep(1000);
            } catch (IOException e) {
                e.printStackTrace();
                System.out.println("An error occured during the Manifest instrumentation ");
                exit(0);
            } catch (XmlPullParserException e) {
                e.printStackTrace();
                System.out.println("An error occured during the Manifest instrumentation ");
                exit(0);
            } catch (Exception e) {
                e.printStackTrace();
                System.out.println("An error occured during the Manifest instrumentation ");
                exit(0);
            }
            if(slice_class != null){
                System.out.println("Slice class found. Extracting the slice...");
                if(Instrumenter.DEBUG){
                    System.out.println("DEBUG : Slice class is "+slice_class.getName());

                }
                try {
                    SootClass slice_class_parsed = config.parse_jimple(i.getAbsolutePath()+"/"+slice_class.getName()+".jimple");
                    SootMethod sm = slice_class_parsed.getMethods().get(0);
                    String replace_body_type ="";
                    File get_class = new File(i.getAbsolutePath()+"/class_of_extraction.txt");
                    if(get_class.exists()) {
                        try (BufferedReader br = new BufferedReader(new FileReader(get_class))) {
                            for (String line; (line = br.readLine()) != null; ) {
                                replace_body_type = line;
                            }
                        } catch (IOException e) {
                            e.printStackTrace();
                        }
                    }
                    Body b = sm.getActiveBody();
                    ArrayList<Local> locals = new ArrayList<>(b.getLocals());
                    ArrayList<Local> to_slice =utility2.clear_Local_list(locals,replace_body_type);
                    My_slice slice = new My_slice(to_slice,utility2.clear_Unit_list(b.getUnits(),to_slice));
                    if(Instrumenter.DEBUG){
                        System.out.println("DEBUG : Slice Extracted\n\n");
                        System.out.println(slice.toString());
                    }
                    config.add_dependencies(slice);
                    slice_corrispondence.put(i.getName(), slice);
                    slice_class.setLibraryClass();
                } catch (LexerException e) {
                    e.printStackTrace();
                } catch (IOException e) {
                    e.printStackTrace();
                } catch (ParserException e) {
                    e.printStackTrace();
                }catch (RuntimeException e){
                    e.printStackTrace();
                }catch (Exception e){
                    e.printStackTrace();
                }

            }else{
                System.out.println("DEBUG : No slice class found, trying with a Mined slice...");
                String feature="";
                File get_feature = new File(i.getAbsolutePath()+"/slices_classes.txt");
                if(get_feature.exists()) {
                    try (BufferedReader br = new BufferedReader(new FileReader(get_feature))) {
                        for (String line; (line = br.readLine()) != null; ) {
                            if(line.startsWith("Feature")){
                                feature=line.split(":")[1];
                            }
                        }
                    } catch (IOException e) {
                        e.printStackTrace();
                    }
                }

                if(Instrumenter.DEBUG){
                    System.out.println("DEBUG : Gather slices from "+slices_path+"\n\n");
                }
                Gatherer ga = new Gatherer();
                slices_gathered = ga.gather_slices();
                My_slice slice = config.get_random_slice(slices_gathered);
                slices_gathered_used.add(slice);
                slice_corrispondence.put(i.getName(),slice);
            }
        }
        Gatherer ga = new Gatherer();
        ga.remove_unused_slices(slices_gathered_used);
        if(DEBUG){
            System.out.println("The number of total classes after the injection is "+Scene.v().getClasses().size());
            System.out.println("The number of application classes after the injection is "+Scene.v().getApplicationClasses().size());

        }
        System.out.println("Injection of the dependencies done.\nNow focus on the slice injection...\n\n");
        malwares = config.find_malware_classes(goodwares_classes);
        if(DEBUG){
            System.out.println("The number of original malware classes is : "+malwares.size());
            System.out.println("Now calculating the Average CC of the malware...");

        }
        Map<Integer, ArrayList<SootClass>> scores =config.get_scores(malwares);

        Double AVG = config.get_AVG(scores,malwares.size());
        if(DEBUG){
            System.out.println("AVG found :"+AVG);

        }
        config.exclude_slices();

        Injecter injecter = new Injecter();
        for(String name : goodwares_classes.keySet()){
            My_slice slice = slice_corrispondence.get(name);
            int slice_CC = slice.get_CC();
            int delta =0;
            boolean done= false;
            ArrayList<SootClass> possible_inj = new ArrayList<>();
            String opaque_pred = "";
            if(opaque_scores.keySet().size() >1){
                int randomNum = ThreadLocalRandom.current().nextInt(0, opaque_scores.size()-1);
                int i =0;
                for (String s :opaque_scores.keySet()){
                    if(i == randomNum){
                        opaque_pred = s;
                        break;
                    }else{
                        i++;
                    }
                }
            }else{
                Iterator iter = opaque_scores.keySet().iterator();
                opaque_pred = (String) iter.next();
            }
            slice_CC += opaque_scores.get(opaque_pred);
            while(done==false && delta <= AVG+THRESHOLD){
                if(scores.containsKey(AVG.intValue()-slice_CC+delta)) {
                    possible_inj = scores.get(AVG.intValue() - slice_CC + delta);
                    if(possible_inj == null){
                        possible_inj = scores.get(AVG.intValue() - slice_CC - delta);
                    }
                    if(possible_inj != null) {
                        done = injecter.inject(possible_inj, slice, opaque_pred);
                    }
                }
                if(scores.containsKey(!done && scores.containsKey(AVG.intValue()-slice_CC-delta))) {
                    possible_inj = scores.get(AVG.intValue() - slice_CC + delta);
                    if(possible_inj == null){
                        possible_inj = scores.get(AVG.intValue() - slice_CC - delta);
                    }
                    if(possible_inj != null) {
                        done = injecter.inject(possible_inj, slice, opaque_pred);
                    }
                }
                delta++;

            }
            if(done==false){
                System.out.println("ERROR: Injection of goodware  "+name+" was not possible");
                return;
            }
        }



            int classes =0;
            float AVG_tot = 0;
            for(SootClass cc : Scene.v().getClasses()){
                if(!config.isExcludeClass(cc.getName())){
                    AVG_tot += utility2.calculate_cyclomatic_complexity(cc);
                    classes+=1;

                }
            }

            System.out.println("AVG CC final :"+Math.round(AVG_tot)/classes);
            System.out.println("The number of Application classes at the end is "+ config.count_classes().size());
            PackManager.v().writeOutput(); //writes the final apk
            System.out.println("Injection done :) ");
            return;
        }
    }
