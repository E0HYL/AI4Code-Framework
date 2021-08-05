
import org.xmlpull.v1.XmlPullParserException;


import soot.*;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;
import java.util.*;

import static java.lang.System.exit;



public class Instrumenter {




    private static String dexPath = "";

    private static String apkPath = "";

    public static String AndroidSdk = "";


    private static final int THRESHOLD = 50;

    public static final boolean DEBUG = true;





    public static void main(String[] args) {


        if(args.length == 3){
            apkPath = args[0];
            dexPath = args[1];
            AndroidSdk = args[2];
        }else{
            System.out.println("Wrong arguments, invocation should be like:\njava -jar injector.jar <malware_apk> <path_to_jimple_files> <Android_sdk_path> \n");
            exit(0);
        }
        System.out.println("Configuring the framework..");
        Soot_utlilty config = new Soot_utlilty();
        if(DEBUG){
            System.out.println("DEBUG : apk at "+apkPath+", jimples to inject in "+dexPath+"\n\n");
        }
        config.initSoot(apkPath,new File(dexPath));
        Manifest_extractor man_extractor = new Manifest_extractor();
        File[] directories = config.get_directories(dexPath);
        Map<String,My_slice> slice_corrispondence = new HashMap<>();
        Map<String,ArrayList<String>> goodwares_classes = new HashMap<>();
        ArrayList<SootClass> malwares = new ArrayList<>();
        Jimple_utility utility2= new Jimple_utility();
        if(DEBUG){
            System.out.println("DEBUG : Load classes to the Scene");
        }
        File i = new File(dexPath);
            SootClass slice_class= null;
            ArrayList<String> classes = config.get_goodware_classes(i);
            goodwares_classes.put(i.getName(),classes);
            for(String s : classes){
                if (!s.startsWith("Slice")){
                    SootClass sc = Scene.v().getSootClass(s);
                    sc.setApplicationClass();
                }else{
                    if(!Scene.v().getSootClass(s).isPhantom()) {
                        slice_class = Scene.v().getSootClass(s);
                   }
                }
            }
            System.out.println("Injecting new components into the manifest\n");
            try {
                man_extractor.addProperties(classes,apkPath,i.getAbsolutePath(),null);
                Thread.sleep(1000);
            } catch (IOException e) {
                e.printStackTrace();
            } catch (XmlPullParserException e) {
                e.printStackTrace();
            }catch (Exception e) {
                e.printStackTrace();
            }
            if(slice_class != null){
                System.out.println("Slice class found. Extracting the slice...");
                if(Instrumenter.DEBUG){
                    System.out.println("DEBUG : Slice class is "+slice_class.getName());

                }
                SootMethod sm = slice_class.getMethods().get(0);
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
            }
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
        Injecter injecter = new Injecter();
        for(String name : goodwares_classes.keySet()){
            My_slice slice = slice_corrispondence.get(name);
            if(slice!=null){
            int slice_CC = slice.get_CC();
            int delta =0;
            boolean done= false;

            ArrayList<SootClass> possible_inj = new ArrayList<>();
            while(done==false && delta <= AVG+THRESHOLD) {

                if (scores.containsKey(AVG.intValue() - slice_CC + delta) ) {
                    possible_inj = scores.get(AVG.intValue() - slice_CC + delta);
                    if (possible_inj == null) {
                        possible_inj = scores.get(AVG.intValue() - slice_CC - delta);
                    }
                    if (possible_inj != null) {
                        done = injecter.inject(possible_inj, slice,"");
                    }
                }
                if(scores.containsKey(!done && scores.containsKey(AVG.intValue()-slice_CC-delta))) {
                    possible_inj = scores.get(AVG.intValue() - slice_CC + delta);
                    if(possible_inj == null){
                        possible_inj = scores.get(AVG.intValue() - slice_CC - delta);
                    }
                    if(possible_inj != null) {
                        done = injecter.inject(possible_inj, slice, "");
                    }
                }
                delta++;
            }

            }else{
                System.out.println("Cannot simulate the slice injection cause this feature has no slice :)");
            }


        }

        System.out.println("Injection done :) ");



        config.exclude_slices();


        PackManager.v().writeOutput();


    }
}