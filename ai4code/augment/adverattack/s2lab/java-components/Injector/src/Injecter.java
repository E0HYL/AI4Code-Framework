import soot.*;
import soot.jimple.*;

import soot.jimple.parser.lexer.LexerException;

import soot.jimple.parser.parser.ParserException;
import soot.util.Chain;


import java.io.*;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.concurrent.ThreadLocalRandom;

public class Injecter {

    private Soot_utlilty config = new Soot_utlilty();
    private ArrayList<SootClass> already_injected = new ArrayList<>();


    public boolean inject_slice(My_slice to_inject, SootMethod injected,String opaque_path){
        ArrayList<Unit> units_to_inj = to_inject.getMy_units();
        ArrayList<Local> locals_to_inj = to_inject.getMy_locals();
        if(!injected.hasActiveBody()){
            System.out.println("This method has no active body!");
            return false;
        }
        My_slice to_inject_final = retrieve_3SAT(units_to_inj,locals_to_inj,opaque_path);
        ArrayList<Unit> units_to_inj_final = to_inject_final.getMy_units();
        ArrayList<Local> locals_to_inj_final = to_inject_final.getMy_locals();
        Body b = injected.getActiveBody();
        System.out.println("ORIGINAL\n"+b.toString());
        for (Local lo : locals_to_inj_final){
            if(!b.getLocals().contains(lo)){
                b.getLocals().add(lo);
            }
        }
        ArrayList<Unit> extremis = this.findExtremis(b);
        if(!extremis.isEmpty() && !(extremis.size() == 1)){
            Unit start = extremis.get(0);
            extremis.remove(start);
            try {
                b.getUnits().insertAfter(units_to_inj_final, start);
                if(!(extremis.get(0) instanceof ReturnVoidStmt)) {
                    int size = units_to_inj_final.size();
                    Unit final_u = units_to_inj_final.get(size - 1);

                    b.getUnits().remove(final_u);
                }else{
                    b.getUnits().remove(extremis.get(0));
                }
            }catch (Exception e){
                return false;
            }

            if(Instrumenter.DEBUG) {
                System.out.println("Final Jimple code\n" + b.toString());

            }
            b.validate();
            return true;
        }
        return false;
    }

    private ArrayList<Unit> findExtremis(Body activeBody) {
        ArrayList<Unit> tmp = new ArrayList<>();
        UnitPatchingChain units =activeBody.getUnits();
        int max_number = units.size();
        int min =0;
        for(Iterator<Unit> iter = units.iterator();iter.hasNext();){
            Unit tmp_u =iter.next();
            if(tmp_u instanceof IdentityStmt){
                min++;
            }else{
                break;
            }
        }
        if( min < max_number -1) {
            int randomNum = ThreadLocalRandom.current().nextInt(min, max_number - 1);
            int i = 0;
            for (Iterator<Unit> iter = units.iterator(); iter.hasNext(); ) {
                Unit tmp_u = iter.next();
                if (i >= randomNum) {
                    tmp.add(tmp_u);
                }
                i++;
            }
        }
        return  tmp;
    }

    private My_slice retrieve_3SAT(ArrayList<Unit> units_to_inject, ArrayList<Local> locals_to_inject,String opaque_path){

        SootMethod method = new SootMethod("tmp",
                null,
                VoidType.v(), Modifier.PUBLIC );
        Body tmp_b = Jimple.v().newBody(method);
        String path = opaque_path;
        try {

            SootClass opaque = config.parse_jimple(path);
            SootMethod opaques = opaque.getMethod("void opaque()");
            Chain<Local> tmp_local;
            ArrayList<Local> to_prune = new ArrayList<>();
            UnitPatchingChain tmp_units;
            ArrayList<Unit> to_prune_units = new ArrayList<>();
            Body opaque_b = opaques.getActiveBody();
            tmp_local = opaque_b.getLocals();
            tmp_units = opaque_b.getUnits();
            tmp_b.getLocals().addAll(tmp_local);
            tmp_b.getUnits().addAll(tmp_units);
            for ( Local l : tmp_b.getLocals()){
                if(l.getType().toString() == opaque.getName() || l.getType().toString() == "java.io.PrintStream"){
                    to_prune.add(l);
                }
            }
            for (Local lo : locals_to_inject){
                if(!tmp_b.getLocals().contains(lo)){
                    tmp_b.getLocals().add(lo);
                }
            }
            Unit injection = null;
            for (Iterator<Unit> iter = tmp_b.getUnits().iterator(); iter.hasNext();){
                Unit u = iter.next();
                boolean to_pru = false;
                for (ValueBox v : u.getUseAndDefBoxes()){
                    if(to_prune.contains(v.getValue())){
                        to_pru= true;
                        to_prune_units.add(u);
                    }
                }
                if(to_pru){
                    if (u.getBoxesPointingToThis().size() > 0){
                        injection = u;
                    }
                }
            }
            ArrayList<Unit> tmp_un = new ArrayList<>();
            for(Unit ut : units_to_inject){
                if(!(ut instanceof ReturnVoidStmt)){
                    tmp_un.add(ut);
                }
            }
            tmp_b.getUnits().insertAfter(tmp_un,injection);
            for(Local l : to_prune){
                tmp_b.getLocals().remove(l);
            }
            for(Unit u : to_prune_units){
                tmp_b.getUnits().remove(u);
            }
            ArrayList<Unit> final_units = new ArrayList<>();
            ArrayList<Local> final_locals = new ArrayList<>();
            for(Local l : tmp_b.getLocals()){
                final_locals.add(l);
            }
            for(Unit u : tmp_b.getUnits()){
                final_units.add(u);
            }
            My_slice to_ret = new My_slice(final_locals,final_units);
            return to_ret;

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
        return null;



    }


    public boolean inject(ArrayList<SootClass> possible_inj,My_slice slice,String opaque_path){
        boolean done = false;
        for(int i=0; i< possible_inj.size(); i++){
            SootClass tmp_c = possible_inj.get(i);
            if(config.isExcludedLibrary_noASexc(tmp_c.getName()) || already_injected.contains(tmp_c) || tmp_c.isLibraryClass()  ||  tmp_c.getName().contains("MainActivity"))  continue;
            for(SootMethod m : tmp_c.getMethods()){
                if(!m.hasActiveBody() || config.isExcludedMethod(m.getName())){
                    continue;
                }
                slice.fix_this_ref(tmp_c);
                Injecter inj = new Injecter();
                done =inj.inject_slice(slice,m,opaque_path);
                if(done) break;
            }
            if(done){
                System.out.println("Chosen class "+tmp_c.getName());
                already_injected.add(tmp_c);
                break;
            }

        }
        return done;
    }

}
