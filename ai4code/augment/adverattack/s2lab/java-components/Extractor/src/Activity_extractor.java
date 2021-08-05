
import soot.*;
import soot.SootClass;
import soot.jimple.IfStmt;
import soot.jimple.ReturnStmt;
import soot.jimple.ReturnVoidStmt;
import soot.toolkits.graph.Block;
import soot.toolkits.graph.ExceptionalBlockGraph;
import soot.toolkits.graph.ExceptionalUnitGraph;
import soot.toolkits.graph.pdg.*;
import soot.util.Chain;
import java.util.*;


public class Activity_extractor {


    private Soot_utlilty utility = new Soot_utlilty();



    public   ArrayList<String> extract_activity_dependencies_PDG(ArrayList<String> dependencies, String feature){
        ArrayList<String> new_dep = new ArrayList<String>();
        if(!dependencies.contains(feature)){
            dependencies.add(feature);
        }
        for (SootClass c : Scene.v().getApplicationClasses()) {
            if(c.getName().equals(feature)){
                Chain<SootClass> interfaces = c.getInterfaces();
                Chain<SootField> fields = c.getFields();
                List<SootMethod> methods = c.getMethods();

                if(c.hasSuperclass()){
                    SootClass superclass = c.getSuperclass();
                    if (!utility.isExcludeClass(superclass)) {
                        new_dep.add(superclass.getName());
                    }
                }


                for(Iterator<SootField> iter = fields.iterator(); iter.hasNext();){
                    SootField field= iter.next();
                    if (!utility.isExcludeClass(field.getType().toString()) && !field.getType().toString().contains("[]")) {
                        if (!dependencies.contains(field.getType().toString()) && !new_dep.contains(field.getType().toString())) {
                            new_dep.add(field.getType().toString());
                        }
                    }

                }
                //handle interfaces
                for(Iterator<SootClass> iter = interfaces.iterator(); iter.hasNext();){
                    SootClass field= iter.next();
                    if (!utility.isExcludeClass(field.getType().toString())) {
                        if (!dependencies.contains(field.getType().toString()) && !new_dep.contains(field.getType().toString())) {
                            new_dep.add(field.getType().toString());
                        }
                    }

                }

                for (SootMethod m : methods ){
                    if (!m.hasActiveBody()) {
                        continue;
                    }
                    Body b = m.getActiveBody();
                    boolean able =true;
                    try{
                    ExceptionalUnitGraph CFG = new ExceptionalUnitGraph(b);
                    HashMutablePDG PDG = new HashMutablePDG(CFG);
                    for(Iterator <PDGNode> iter = PDG.iterator(); iter.hasNext();){
                        PDGNode node = iter.next();
                        for (PDGNode a : node.getDependents()){
                                Block block = (Block) a.getNode();
                                for (Iterator<Unit> iter_u = block.iterator(); iter_u.hasNext();){
                                    Unit unit = iter_u.next();
                                    for (ValueBox v : unit.getUseAndDefBoxes()){
                                        String tmp_feat =v.getValue().getType().toString();
                                        if(!dependencies.contains(tmp_feat) && !utility.isExcludeClass(tmp_feat) && !new_dep.contains(tmp_feat)  && !tmp_feat.contains("[")){
                                            new_dep.add(tmp_feat);
                                        }
                                        String tmp =v.getValue().toString();
                                        if (tmp.startsWith("class")){
                                            String dep = tmp.split("\"")[1].split(";")[0].substring(1).replace("/",".");
                                            if (!utility.isExcludeClass(dep) && !dep.contains("[]") && dep!= feature){
                                                if(!dep.equals(c.getName()) ){
                                                    if(!dependencies.contains(dep) && !new_dep.contains(dep) ){
                                                        new_dep.add(dep);
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }

                       }
                    }
                    }catch(Exception e){
                            able = false;
                    }
                    if (able == false){
                        for (Iterator<Local> iter_local = b.getLocals().iterator(); iter_local.hasNext();){
                            Local local_tmp = iter_local.next();
                            if (!utility.isExcludeClass(local_tmp.getType().toString()) && !local_tmp.getType().toString().contains("[]")){
                                if(!local_tmp.getType().toString().equals(c.getName()) ){
                                    if(!dependencies.contains(local_tmp.getType().toString()) && !new_dep.contains(local_tmp.getType().toString())){
                                        new_dep.add(local_tmp.getType().toString());
                                    }
                                }
                            }
                        }
                        for (Iterator<ValueBox> iter_units = b.getUseAndDefBoxes().iterator() ; iter_units.hasNext();){
                            ValueBox value = iter_units.next();
                            String tmp_feat =value.getValue().getType().toString();
                            if(!dependencies.contains(tmp_feat) && !utility.isExcludeClass(tmp_feat) && !new_dep.contains(tmp_feat)  && !tmp_feat.contains("[")){
                                new_dep.add(tmp_feat);
                            }
                            String tmp =value.getValue().toString();
                            if (tmp.startsWith("class")){
                                String dep = tmp.split("\"")[1].split(";")[0].substring(1).replace("/",".");
                                if (!utility.isExcludeClass(dep) && !dep.contains("[]") && dep!= feature){
                                    if(!dep.equals(c.getName()) ){
                                        if(!dependencies.contains(dep) && !new_dep.contains(dep) ){
                                            new_dep.add(dep);
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        if (new_dep.size() >0){
            dependencies.addAll(new_dep);
            for (String i : new_dep){
                if (i != feature){
                    ArrayList<String> tmp_dep = extract_activity_dependencies_PDG(dependencies,i);
                    if(tmp_dep.size() >0) {
                        for (String s : tmp_dep) {
                            if (!dependencies.contains(s)) {
                                dependencies.add(s);
                            }
                        }
                    }
                }
            }
        }
        if(!dependencies.contains(feature)) {
            dependencies.add(feature);
        }
        Set<String> foo = new HashSet<String>(dependencies);
        ArrayList<String> mainList = new ArrayList<String>();
        mainList.addAll(foo);
        return mainList;
    }



    public   ArrayList<String> extract_activity_dependencies_PDG_soft(ArrayList<String> dependencies, String feature){
        ArrayList<String> new_dep = new ArrayList<String>();
        if(!dependencies.contains(feature)){
            dependencies.add(feature);
        }
        for (SootClass c : Scene.v().getApplicationClasses()) {
            if(c.getName().contains(feature)){
                Chain<SootClass> interfaces = c.getInterfaces();
                Chain<SootField> fields = c.getFields();
                List<SootMethod> methods = c.getMethods();

                if(c.hasSuperclass()){
                    SootClass superclass = c.getSuperclass();
                    if (!utility.isExcludeClass(superclass)) {
                        new_dep.add(superclass.getName());
                    }
                }


                for(Iterator<SootField> iter = fields.iterator(); iter.hasNext();){
                    SootField field= iter.next();
                    if (!utility.isExcludeClass(field.getType().toString()) && !field.getType().toString().contains("[]")) {
                        if (!dependencies.contains(field.getType().toString()) && !new_dep.contains(field.getType().toString())) {
                            new_dep.add(field.getType().toString());
                        }
                    }

                }
                //handle interfaces
                for(Iterator<SootClass> iter = interfaces.iterator(); iter.hasNext();){
                    SootClass field= iter.next();
                    if (!utility.isExcludeClass(field.getType().toString())) {
                        if (!dependencies.contains(field.getType().toString()) && !new_dep.contains(field.getType().toString())) {
                            new_dep.add(field.getType().toString());
                        }
                    }

                }

                for (SootMethod m : methods ){
                    if (!m.hasActiveBody()) {
                        continue;
                    }
                    Body b = m.getActiveBody();
                    boolean able =true;
                    try{
                        ExceptionalUnitGraph CFG = new ExceptionalUnitGraph(b);
                        HashMutablePDG PDG = new HashMutablePDG(CFG);
                        for(Iterator <PDGNode> iter = PDG.iterator(); iter.hasNext();){
                            PDGNode node = iter.next();
                            for (PDGNode a : node.getDependents()){
                                Block block = (Block) a.getNode();
                                for (Iterator<Unit> iter_u = block.iterator(); iter_u.hasNext();){
                                    Unit unit = iter_u.next();
                                    for (ValueBox v : unit.getUseAndDefBoxes()){
                                        String tmp_feat =v.getValue().getType().toString();
                                        if(!dependencies.contains(tmp_feat) && !utility.isExcludeClass(tmp_feat) && !new_dep.contains(tmp_feat)  && !tmp_feat.contains("[")){
                                            new_dep.add(tmp_feat);
                                        }
                                        String tmp =v.getValue().toString();
                                        if (tmp.startsWith("class")){
                                            String dep = tmp.split("\"")[1].split(";")[0].substring(1).replace("/",".");
                                            if (!utility.isExcludeClass(dep) && !dep.contains("[]") && dep!= feature){
                                                if(!dep.equals(c.getName()) ){
                                                    if(!dependencies.contains(dep) && !new_dep.contains(dep) ){
                                                        new_dep.add(dep);
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }

                            }
                        }
                    }catch(Exception e){
                        able = false;
                    }
                    if (able == false){
                        if(Instrumenter.DEBUG) {
                            System.out.println("Impossible to extract Block\nTrying Manually...\n");
                        }
                        for (Iterator<Local> iter_local = b.getLocals().iterator(); iter_local.hasNext();){
                            Local local_tmp = iter_local.next();
                            if (!utility.isExcludeClass(local_tmp.getType().toString()) && !local_tmp.getType().toString().contains("[]")){
                                if(!local_tmp.getType().toString().equals(c.getName()) ){
                                    if(!dependencies.contains(local_tmp.getType().toString()) && !new_dep.contains(local_tmp.getType().toString())){
                                        new_dep.add(local_tmp.getType().toString());
                                    }
                                }
                            }
                        }
                        for (Iterator<ValueBox> iter_units = b.getUseAndDefBoxes().iterator() ; iter_units.hasNext();){
                            ValueBox value = iter_units.next();
                            String tmp_feat =value.getValue().getType().toString();
                            if(!dependencies.contains(tmp_feat) && !utility.isExcludeClass(tmp_feat) && !new_dep.contains(tmp_feat)  && !tmp_feat.contains("[")){
                                new_dep.add(tmp_feat);
                            }
                            String tmp =value.getValue().toString();
                            if (tmp.startsWith("class")){
                                String dep = tmp.split("\"")[1].split(";")[0].substring(1).replace("/",".");
                                if (!utility.isExcludeClass(dep) && !dep.contains("[]") && dep!= feature){
                                    if(!dep.equals(c.getName()) ){
                                        if(!dependencies.contains(dep) && !new_dep.contains(dep) ){
                                            new_dep.add(dep);
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        if (new_dep.size() >0){
            dependencies.addAll(new_dep);
            for (String i : new_dep){
                System.out.println(i);
                if (i != feature){
                    ArrayList<String> tmp_dep = extract_activity_dependencies_PDG(dependencies,i);
                    if(tmp_dep.size() >0) {
                        for (String s : tmp_dep) {
                            if (!dependencies.contains(s)) {
                                dependencies.add(s);
                            }
                        }
                    }
                }
            }
        }
        if(!dependencies.contains(feature)) {
            dependencies.add(feature);
        }
        Set<String> foo = new HashSet<String>(dependencies);
        ArrayList<String> mainList = new ArrayList<String>();
        mainList.addAll(foo);
        return mainList;
    }



    public void extract_classes(ArrayList<String> dependencies,  String apk_path) {
        if(Instrumenter.DEBUG) {
            System.out.println("Dependencies found "+dependencies);
        }
        String out = "";
        for(Iterator<SootClass> iter_main = Scene.v().getApplicationClasses().snapshotIterator(); iter_main.hasNext();){
            SootClass c = iter_main.next();

            if(!dependencies.contains(c.getName()) || c.getName().contains("[]")){
                c.setPhantomClass();
            }else{

                c.setApplicationClass();
                out = out+c.getName()+"\n";

            }
        }
        if(out.length()>5) {
            utility.WriteFile("classes.txt", out);
        }
    }


    public ArrayList<My_slice> identify_startActivity(String feature) {

        ArrayList<String> soot_classes = new ArrayList<>();

        ArrayList<My_slice> soot_slice = new ArrayList<>();
        System.out.println("Trying to extract slice Activity invocation : " + feature);
        for (SootClass c : Scene.v().getApplicationClasses()) {

            if (utility.isExcludeClass(c)) {
                continue;
            }

            for (SootMethod m : c.getMethods()) {
                if(!m.hasActiveBody()){
                    continue;
                }

                if (m.getActiveBody().toString().contains(utility.to_smali(feature)) && m.getActiveBody().toString().contains("startActivity")) {

                    Body b = m.getActiveBody();
                    if(Instrumenter.DEBUG) {
                        System.out.println("DEBUG : Getting CFG");
                    }
                    ExceptionalUnitGraph CFG = new ExceptionalUnitGraph(b);
                    ExceptionalBlockGraph BFG = new ExceptionalBlockGraph(CFG);
                    if(Instrumenter.DEBUG) {
                        System.out.println("DEBUG : Start searching Intent invocation into the CFG");
                    }
                    for(Iterator<Block> iter = BFG.iterator(); iter.hasNext();){
                        Block block = iter.next();

                        if(block.toString().contains(utility.to_smali(feature)) && block.toString().contains("startActivity")){
                            if(Instrumenter.DEBUG) {
                                System.out.println("DEBUG : Intent and startActivity in the same block :D ");
                            }
                            ArrayList<Unit> units = new ArrayList<>();
                            for(Iterator<Unit> iter_block = block.iterator(); iter_block.hasNext();){
                                units.add(iter_block.next());
                            }
                            ArrayList<String> missing_names = this.missing_values_units(units);
                            if(!missing_names.isEmpty()){
                                ArrayList<Unit> missing_units = new ArrayList<>();
                                for(String missing : missing_names ){
                                    for (Iterator<Unit> iter_un = block.getBody().getUnits().iterator(); iter_un.hasNext(); ) {
                                        Unit un = iter_un.next();
                                        List<ValueBox> def = un.getDefBoxes();
                                        if(!def.isEmpty()){
                                            for (Iterator<ValueBox> iter_def = def.iterator(); iter_def.hasNext(); ) {
                                                ValueBox def_ = iter_def.next();
                                                if (def_.getValue().toString().equals(missing)) {
                                                    missing_units.add(un);
                                                }
                                            }
                                        }
                                    }
                                }
                                units.addAll(0,missing_units);
                            }
                            ArrayList<String> locals_to_add = new ArrayList<>();
                            for (Iterator<Unit> iter_un = units.iterator(); iter_un.hasNext(); ) {
                                Unit un = iter_un.next();
                                List<ValueBox> def = un.getDefBoxes();
                                for (Iterator<ValueBox> iter_def = def.iterator(); iter_def.hasNext(); ) {
                                    ValueBox def_ = iter_def.next();
                                    if (!locals_to_add.contains(def_.getValue().toString())) {
                                        locals_to_add.add(def_.getValue().toString());
                                    }
                                }

                            }
                            ArrayList<Local> locals_to_export= new ArrayList<>();
                            for(Iterator<Local> iter_locals = m.getActiveBody().getLocals().iterator();iter_locals.hasNext();){
                                Local tmp_local = iter_locals.next();
                                if(locals_to_add.contains(tmp_local.getName())){
                                    locals_to_export.add(tmp_local);
                                }
                            }
                            My_slice slice = new My_slice(locals_to_export,units);
                            slice.setFeature(c.getName());

                            soot_slice.add(slice);
                            if(!soot_classes.contains(c.getName())){
                                soot_classes.add(c.getName()+":"+m.getName());
                            }
                        }else if (block.toString().contains(utility.to_smali(feature)) && !block.toString().contains("startActivity")){
                            if(Instrumenter.DEBUG) {
                                System.out.println("DEBUG : Intent and startActivity in different blocks, trying extracting...");
                            }


                            if(Instrumenter.DEBUG) {
                                System.out.println("DEBUG : Searching for a correct path in order to retrieve the needed code...  ");
                            }
                            ArrayList<Block> my_blocks = find_path_for_startActivity(new ArrayList<Block>(),new ArrayList<Block>(), block);
                            ArrayList<Unit> units = new ArrayList<>();
                            for(Block blo : my_blocks) {
                                for (Iterator<Unit> iter_block = blo.iterator(); iter_block.hasNext(); ) {
                                    Unit un =iter_block.next();
                                    if(!(un instanceof ReturnStmt || un instanceof ReturnVoidStmt)) {
                                        if(un instanceof IfStmt){
                                            UnitBox ubox =((IfStmt) un).getTargetBox();
                                            Unit unit = ubox.getUnit();
                                            boolean in= false;
                                            for(Block bl : my_blocks){
                                                for (Iterator<Unit> iter_blocks = bl.iterator(); iter_block.hasNext(); ) {
                                                    if(iter_blocks.next() == unit){
                                                        in = true;
                                                    }
                                                }
                                            }
                                            if(in){
                                                units.add(un);
                                            }
                                        }else{
                                            units.add(un);

                                        }
                                    }
                                }
                            }
                            ArrayList<String> missing_names = this.missing_values_units(units);
                            if(!missing_names.isEmpty()){
                                ArrayList<Unit> missing_units = new ArrayList<>();
                                for(String missing : missing_names ){
                                    for (Iterator<Unit> iter_un = block.getBody().getUnits().iterator(); iter_un.hasNext(); ) {
                                        Unit un = iter_un.next();
                                        List<ValueBox> def = un.getDefBoxes();
                                        if(!def.isEmpty()){
                                            for (Iterator<ValueBox> iter_def = def.iterator(); iter_def.hasNext(); ) {
                                                ValueBox def_ = iter_def.next();
                                                if (def_.getValue().toString().equals(missing)) {
                                                    missing_units.add(un);
                                                }
                                            }
                                        }
                                    }
                                }
                                units.addAll(0,missing_units);
                            }

                            ArrayList<String> locals_to_add = new ArrayList<>();

                            for (Iterator<Unit> iter_un = units.iterator(); iter_un.hasNext(); ) {
                                Unit un = iter_un.next();
                                List<ValueBox> def = un.getDefBoxes();
                                for (Iterator<ValueBox> iter_def = def.iterator(); iter_def.hasNext(); ) {
                                    ValueBox def_ = iter_def.next();
                                    if (!locals_to_add.contains(def_.getValue().toString())) {
                                        locals_to_add.add(def_.getValue().toString());
                                    }
                                }
                            }
                            ArrayList<Local> locals_to_export= new ArrayList<>();
                            for(Iterator<Local> iter_locals = m.getActiveBody().getLocals().iterator();iter_locals.hasNext();){
                                Local tmp_local = iter_locals.next();
                                if(locals_to_add.contains(tmp_local.getName())){
                                    locals_to_export.add(tmp_local);
                                }
                            }




                            My_slice slice = new My_slice(locals_to_export,units);
                            slice.setFeature(c.getName());
                            soot_slice.add(slice);
                            if(!soot_classes.contains(c.getName())){
                                soot_classes.add(c.getName()+":"+m.getName());
                            }
                        }

                    }

                }
            }
        }
        for(My_slice sl : soot_slice){
            this.add_dependencies(sl);
        }
        String to_out = "Feature : "+feature+"\n";
        for (String s : soot_classes){
            to_out= to_out +s +"\n";
        }
        if(Instrumenter.DEBUG) {
            System.out.println("DEBUG : writing file  ./slices_classes.txt ");
        }
        utility.WriteFile("slices_classes.txt", to_out);
        return soot_slice;
    }


    private ArrayList<Block> find_path_for_startActivity(ArrayList<Block> visited,ArrayList<Block> final_path, Block b){
        String searched= "startActivity";

        if(b.toString().contains(searched)){
            if(!final_path.contains(b)) {
                final_path.add(b);
            }
        }else{
            visited.add(b);
            List<Block> succ = b.getSuccs();
            if(succ.size()>0) {
                for (Block block : succ) {
                    if(visited.contains(block)){
                       continue;
                    }else{
                        if(!final_path.contains(b)) {
                            final_path.add(b);
                        }
                        find_path_for_startActivity(visited,final_path,block);
                    }
                }
            }
        }
        return  final_path;
    }






    private ArrayList<String> missing_values_units(ArrayList<Unit> slice) {
        ArrayList<String> tmp = new ArrayList<>();

        for (Iterator<Unit> iter = slice.iterator(); iter.hasNext(); ) {
            Unit un = iter.next();
            List<ValueBox> values = un.getUseBoxes();
            for(Iterator<ValueBox> iter_use = values.iterator(); iter_use.hasNext();){
                ValueBox use = iter_use.next();
                if(use.getValue().toString().startsWith("$") && use.getValue().toString().length() <= 4 && !tmp.contains(use.getValue().toString())){
                    tmp.add(use.getValue().toString());
                }
            }
        }
        for (Iterator<Unit> iter = slice.iterator(); iter.hasNext(); ) {
            Unit un = iter.next();
            List<ValueBox> def= un.getDefBoxes();
            if(!def.isEmpty()) {
                for (Iterator<ValueBox> iter_def = def.iterator(); iter_def.hasNext(); ) {
                    ValueBox def_ = iter_def.next();
                    if (def_.getValue().toString().startsWith("$") && tmp.contains(def_.getValue().toString())) {
                        tmp.remove(def_.getValue().toString());
                    }
                }
            }
        }
        return tmp;

    }

    public void  add_dependencies(My_slice slice){
        ArrayList<Unit> units = slice.getMy_units();
        ArrayList<Local> locals = slice.getMy_locals();
        for(Unit u : units){
            for(ValueBox v : u.getUseAndDefBoxes()){
                if(!utility.isExcludeClass(v.getValue().getType().toString())) {
                    for(String s : extract_activity_dependencies_PDG(new ArrayList<String>(),v.getValue().getType().toString())){
                        SootClass sc = Scene.v().getSootClass(s);
                        sc.setApplicationClass();
                    }
                }
            }
        }
        for(Local l : locals){
            if(!utility.isExcludeClass(l.getType().toString())) {
                for(String s : extract_activity_dependencies_PDG(new ArrayList<String>(),l.getType().toString())){
                    SootClass sc = Scene.v().getSootClass(s);
                    sc.setApplicationClass();
                }
            }
        }
    }


    public ArrayList<My_slice>  extract_method_call_method(SootClass class_of_url, SootMethod method_containing, SootMethod method_searched) {
        ArrayList<My_slice> soot_slice = new ArrayList<>();


        System.out.println("Trying to extract method "+method_searched.getSignature()+" from "+class_of_url.getName()+" contained in method "+method_containing.getSignature());

        if(method_searched.getSignature().contains("<clinit>")){

        }

        for (SootMethod m : class_of_url.getMethods()) {
            if (!m.hasActiveBody()) {
                continue;
            }
            Body b = m.getActiveBody();
            if (b.toString().contains(method_searched.getSignature()) && m.getSignature().equals(method_containing.getSignature())) {

                ExceptionalUnitGraph CFG = new ExceptionalUnitGraph(b);
                ExceptionalBlockGraph BFG = new ExceptionalBlockGraph(CFG);
                for (Iterator<Block> iter = BFG.iterator(); iter.hasNext(); ) {
                    Block block = iter.next();
                    if (block.toString().contains(method_searched.getSignature())) {
                        ArrayList<Unit> units = new ArrayList<>();
                        boolean after = false;
                        for(Iterator<Unit> iter_block = block.iterator(); iter_block.hasNext();){
                            Unit u_tmp = iter_block.next();
                            if(!(u_tmp instanceof IfStmt) && !after) {
                                units.add(u_tmp);
                            }
                            for(ValueBox v : u_tmp.getUseAndDefBoxes()){
                                if(v.getValue().toString().contains(method_searched.getDeclaringClass().getName())){
                                    after=true;
                                    break;
                                }
                            }
                        }
                        ArrayList<String> missing_names = this.missing_values_units(units);
                        if(!missing_names.isEmpty()){
                            ArrayList<Unit> missing_units = new ArrayList<>();
                            for(String missing : missing_names ){
                                for (Iterator<Unit> iter_un = block.getBody().getUnits().iterator(); iter_un.hasNext(); ) {
                                    Unit un = iter_un.next();
                                    List<ValueBox> def = un.getDefBoxes();
                                    if(!def.isEmpty()){
                                        for (Iterator<ValueBox> iter_def = def.iterator(); iter_def.hasNext(); ) {
                                            ValueBox def_ = iter_def.next();
                                            if (def_.getValue().toString().equals(missing)) {
                                                missing_units.add(un);
                                            }
                                        }
                                    }
                                }
                            }
                            units.addAll(0,missing_units);
                        }

                        ArrayList<String> locals_to_add = new ArrayList<>();

                        for (Iterator<Unit> iter_un = units.iterator(); iter_un.hasNext(); ) {
                            Unit un = iter_un.next();
                            List<ValueBox> def = un.getDefBoxes();
                            for (Iterator<ValueBox> iter_def = def.iterator(); iter_def.hasNext(); ) {
                                ValueBox def_ = iter_def.next();
                                if (!locals_to_add.contains(def_.getValue().toString())) {
                                    locals_to_add.add(def_.getValue().toString());
                                }
                            }

                        }
                        ArrayList<Local> locals_to_export= new ArrayList<>();
                        for(Iterator<Local> iter_locals = m.getActiveBody().getLocals().iterator();iter_locals.hasNext();){
                            Local tmp_local = iter_locals.next();
                            if(locals_to_add.contains(tmp_local.getName())){
                                locals_to_export.add(tmp_local);
                            }
                        }
                        My_slice slice = new My_slice(locals_to_export,units);
                        System.out.println(slice.toString());
                        soot_slice.add(slice);

                    }
                }
            }else if (method_searched.getSignature().contains("<clinit>") &&  m.getSignature().equals(method_containing.getSignature()) && b.toString().contains(method_searched.getDeclaringClass().getName()) ){
                if(Instrumenter.DEBUG) {
                    System.out.println("DEBUG : Clinit case ... ");
                }
                ExceptionalUnitGraph CFG = new ExceptionalUnitGraph(b);
                ExceptionalBlockGraph BFG = new ExceptionalBlockGraph(CFG);
                for (Iterator<Block> iter = BFG.iterator(); iter.hasNext(); ) {
                    Block block = iter.next();
                    if (block.toString().contains(method_searched.getDeclaringClass().getName())) {
                        ArrayList<Unit> units = new ArrayList<>();
                        boolean after =false;
                        for(Iterator<Unit> iter_block = block.iterator(); iter_block.hasNext();){
                            Unit u_tmp = iter_block.next();
                            if(!(u_tmp instanceof IfStmt) && !after) {
                                units.add(u_tmp);
                            }
                            for(ValueBox v : u_tmp.getUseAndDefBoxes()){
                                if(v.getValue().toString().contains(method_searched.getDeclaringClass().getName())){
                                    after=true;
                                    break;
                                }
                            }
                        }
                        ArrayList<String> missing_names = this.missing_values_units(units);
                        if(!missing_names.isEmpty()){
                            ArrayList<Unit> missing_units = new ArrayList<>();
                            for(String missing : missing_names ){
                                for (Iterator<Unit> iter_un = block.getBody().getUnits().iterator(); iter_un.hasNext(); ) {
                                    Unit un = iter_un.next();
                                    List<ValueBox> def = un.getDefBoxes();
                                    if(!def.isEmpty()){
                                        for (Iterator<ValueBox> iter_def = def.iterator(); iter_def.hasNext(); ) {
                                            ValueBox def_ = iter_def.next();
                                            if (def_.getValue().toString().equals(missing)) {
                                                missing_units.add(un);
                                            }
                                        }
                                    }
                                }
                            }
                            units.addAll(0,missing_units);
                        }

                        ArrayList<String> locals_to_add = new ArrayList<>();

                        for (Iterator<Unit> iter_un = units.iterator(); iter_un.hasNext(); ) {
                            Unit un = iter_un.next();
                            List<ValueBox> def = un.getDefBoxes();
                            for (Iterator<ValueBox> iter_def = def.iterator(); iter_def.hasNext(); ) {
                                ValueBox def_ = iter_def.next();
                                if (!locals_to_add.contains(def_.getValue().toString())) {
                                    locals_to_add.add(def_.getValue().toString());
                                }
                            }

                        }
                        ArrayList<Local> locals_to_export= new ArrayList<>();
                        for(Iterator<Local> iter_locals = m.getActiveBody().getLocals().iterator();iter_locals.hasNext();){
                            Local tmp_local = iter_locals.next();
                            if(locals_to_add.contains(tmp_local.getName())){
                                locals_to_export.add(tmp_local);
                            }
                        }
                        My_slice slice = new My_slice(locals_to_export,units);
                        System.out.println(slice.toString());
                        soot_slice.add(slice);

                    }
                }
            }
        }
        for(My_slice sl : soot_slice){
            this.add_dependencies(sl);
        }

        if(Instrumenter.DEBUG) {
            System.out.println("DEBUG : writing file  ./slices_classes.txt ");
        }
        return soot_slice;
    }
}
