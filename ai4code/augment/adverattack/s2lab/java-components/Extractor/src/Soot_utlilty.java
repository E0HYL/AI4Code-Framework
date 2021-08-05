import soot.*;

import soot.options.Options;
import soot.tagkit.Tag;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.util.*;

public class Soot_utlilty {
    protected static List<String> excludePackagesList = new ArrayList<String>();
    protected static List<String> primitiveList = new ArrayList<String>();


    static
    {
        excludePackagesList.add("java.");
        excludePackagesList.add("android.");
        excludePackagesList.add("javax.");
        excludePackagesList.add("android.support.");
        excludePackagesList.add("junit.");
        excludePackagesList.add("org.w3c");
        excludePackagesList.add("org.xmlpull");
        excludePackagesList.add("org.xml.sax.");
        excludePackagesList.add("org.json");
        excludePackagesList.add("org.apache.http.");
        excludePackagesList.add("com.google.android");
        excludePackagesList.add("com.android.");
    }

    static
    {
        primitiveList.add("java.");
        primitiveList.add("android.");
        primitiveList.add("javax.");
        primitiveList.add("android.support.");
        primitiveList.add("junit.");
        primitiveList.add("org.w3c");
        primitiveList.add("org.xmlpull");
        primitiveList.add("org.xml.sax.");
        primitiveList.add("org.json");
        primitiveList.add("org.apache.http.");
        primitiveList.add("com.google.android");
        primitiveList.add("com.android.");
        primitiveList.add("int");
        primitiveList.add("String");
        primitiveList.add("dalvik.");
        primitiveList.add("byte");
        primitiveList.add("boolean");
        primitiveList.add("short");
        primitiveList.add("long");
        primitiveList.add("char");
        primitiveList.add("void");
        primitiveList.add("double");
        primitiveList.add("float");
        primitiveList.add("null");
    }





    boolean isExcludeClass(SootClass sootClass)
    {
        if (sootClass.isPhantom())
        {
            return true;
        }

        String packageName = sootClass.getPackageName();
        for (String exclude : primitiveList)
        {
            if (packageName.startsWith(exclude) && !packageName.startsWith("android.support."))
            {
                return true;
            }
        }

        return false;
    }

    boolean isExcludeClass(String sootClass)
    {


        for (String exclude : primitiveList)
        {
            if (sootClass.startsWith(exclude) && !sootClass.startsWith("android.support."))

            {
                return true;
            }
        }

        return false;
    }


    public boolean get_if_ancient (SootClass c,String comparison){
        SootClass tmp= c;
        while(tmp.hasSuperclass()){
            if(!tmp.getName().equals(comparison)) {
                tmp = tmp.getSuperclass();
            }else{
                return true;
            }
        }
        return false;
    }

    //convert to smali name, for matching in jimple files
    public String to_smali(String feature){
        String tmp =feature.replace(".","/");
        tmp= "L"+tmp;
        return  tmp;
    }

    public String to_underline(String feature){
        String tmp =feature.replace(".","_");
          return  tmp;
    }



    //initial Soot settings
    public void initSoot(String apkPath,String output_folder){

        Options.v().set_src_prec(Options.src_prec_apk);

        Options.v().set_output_format(Instrumenter.output_format);

        Options.v().set_output_dir(output_folder);

        String androidJarPath = Scene.v().getAndroidJarPath(Instrumenter.jarsPath, apkPath);

        List<String> pathList = new ArrayList<String>();

        pathList.add(apkPath);

        pathList.add(androidJarPath);

        Options.v().set_process_dir(pathList);

        Options.v().set_force_android_jar(apkPath);

        Options.v().set_keep_line_number(true);

        Options.v().set_process_multiple_dex(true);

        Options.v().set_allow_phantom_refs(true);

        Options.v().set_whole_program(true);

        Options.v().set_wrong_staticness(Options.wrong_staticness_fix);

        Options.v().set_exclude(excludePackagesList);

        Options.v().set_no_bodies_for_excluded(true);

        Scene.v().loadNecessaryClasses();

        PackManager.v().runPacks();

    }

    //Slice Utility
    public My_slice get_simpler_slice(ArrayList<My_slice> slices){
        Map<Double,My_slice> tmp = new TreeMap<>();
        for(My_slice sl : slices){
            try {
                tmp.put(sl.slice_complexity_score(), sl);
            }catch(RuntimeException e){
                System.out.println("Not possible to extract correctly this slice, passing next");
            }
        }

        return ((TreeMap<Double, My_slice>) tmp).firstEntry().getValue();
    }

    public ArrayList<String>  create_dependencies_file(My_slice slice){
        System.out.println("Create slice dependency files ");

        ArrayList<String> slice_dependencies = slice.get_dependencies();
        String out = slice.getName()+"\n";
        for(String s : slice_dependencies){
            out+= s+"\n";
        }
        WriteFile("slice_dependencies.txt",out);
        WriteFile("feature.txt",to_smali(slice.getFeature()));
        return slice_dependencies;
    }

    public void WriteFile(String name,String content){
        File file = new File(Instrumenter.output_dir + "/"+name);
        if(!file.exists()){
            File folder = new File(Instrumenter.output_dir);
            folder.mkdirs();
            try {
                file.createNewFile();
            } catch (IOException e) {
                e.printStackTrace();
            }
        }
        try {
            FileWriter fileWriter = new FileWriter(file);
            fileWriter.write(content);
            fileWriter.flush();
            fileWriter.close();
            if(Instrumenter.DEBUG) {
                System.out.println("DEBUG : New file created : "+file.getAbsolutePath());
            }
        } catch (IOException e) {
            e.printStackTrace();
        }
    }







    public void clean_final_export (){
        ArrayList<SootClass> to_eliminate =new ArrayList<>();
        for (SootClass sc : Scene.v().getApplicationClasses()){
            if(sc.getName().contains("dummy") || sc.getName().contains("java.lang")){
                to_eliminate.add(sc);
            }
        }
        for (SootClass s : to_eliminate){
            s.setPhantomClass();
        }
    }

    public ArrayList<SootMethod> find_method_for_feature(SootClass searched, String feature) {


        ArrayList<SootMethod> to_ret = new ArrayList<>();
        String correspondence = "";
        if(searched.getFields().size()>0){
            for(SootField f : searched.getFields()){
                for(Tag t  :f.getTags()){
                    if(t.toString().contains(feature)){
                        correspondence = feature+"|"+f.getName();
                        break;
                    }
                }

            }
        }
        for(SootMethod m : searched.getMethods()){
            if(!m.hasActiveBody()){
                continue;
            }
            Body b = m.getActiveBody();
            if(correspondence.isEmpty()){
                if(b.toString().contains(feature)){
                    to_ret.add(m);
                }
            }else{
                String field = correspondence.split("\\|")[1];
                if(b.toString().contains(field)){
                    to_ret.add(m);
                }
            }
        }
        return to_ret;
    }
}
