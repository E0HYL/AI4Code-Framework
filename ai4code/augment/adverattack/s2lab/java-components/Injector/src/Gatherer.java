import soot.*;
import soot.jimple.parser.Walker;
import soot.jimple.parser.lexer.Lexer;
import soot.jimple.parser.lexer.LexerException;
import soot.jimple.parser.node.Start;
import soot.jimple.parser.parser.Parser;
import soot.jimple.parser.parser.ParserException;
import soot.util.Chain;
import soot.util.EscapedReader;

import java.io.*;
import java.util.ArrayList;
import java.util.Arrays;

public class Gatherer {

    private static String slices_path = Instrumenter.slices_path;
    private Soot_utlilty util = new Soot_utlilty();
    private Jimple_utility utility2= new Jimple_utility();



    public ArrayList<My_slice> gather_slices(){
        File[] folders = util.get_directories(slices_path);
        ArrayList<My_slice> tmp = new ArrayList<>();
        for(File f : folders){
            for(String s : util.get_class_names(f.getAbsolutePath())){
                if (s.startsWith("Slice")) {
                    try  {
                        SootClass slice = util.parse_jimple(f+"/"+s+".jimple");
                        SootMethod m = slice.getMethods().get(0);
                        Chain<Local> tmp_local;
                        ArrayList<Local> to_prune = new ArrayList<>();
                        UnitPatchingChain tmp_units;
                        ArrayList<Unit> to_prune_units = new ArrayList<>();
                            Body b = m.getActiveBody();
                            String replace_body_type ="";
                            File get_class = new File(f.getAbsolutePath()+"/class_of_extraction.txt");
                            if(get_class.exists()) {
                                try (BufferedReader br = new BufferedReader(new FileReader(get_class))) {
                                    for (String line; (line = br.readLine()) != null; ) {
                                        replace_body_type = line;
                                    }
                                } catch (IOException e) {
                                    e.printStackTrace();
                                }
                            }
                            ArrayList<Local> locals = new ArrayList<>(b.getLocals());
                            ArrayList<Local> to_slice =utility2.clear_Local_list(locals,replace_body_type);
                            My_slice slice_t = new My_slice(to_slice, utility2.clear_Unit_list(b.getUnits(),to_slice));
                            slice_t.setFeature(m.getName());
                            slice_t.setName(f.getAbsolutePath());
                            tmp.add(slice_t);
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
                }

                     else {
                SootClass sc = Scene.v().getSootClass(s);

                sc.setApplicationClass();
                    }
            }
        }
        return tmp;
    }

    public void remove_unused_slices(ArrayList<My_slice> slices_gathered_used) {
        File[] folders = util.get_directories(slices_path);
        for(File f : folders){
            boolean present = false;
            for(My_slice slice : slices_gathered_used){
                if(slice.getName().equals(f.getAbsolutePath())){
                    present=true;
                }
            }
            if(!present){
                for(String s : util.get_class_names(f.getAbsolutePath())){
                    SootClass sc = Scene.v().getSootClass(s);
                    sc.setLibraryClass();
                }
            }

        }

    }
}
